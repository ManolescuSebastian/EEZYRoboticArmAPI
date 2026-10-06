"""Motion service: orchestrates the hardware for the API layer.

Responsibilities:
    * Own the three Stepper instances and the Claw.
    * Run movements on a background thread so HTTP requests return immediately.
    * Support interrupting the current movement via /stop.
    * Record movements for later replay (recording a "session" per hold —
      the API layer coalesces hold-to-move bursts before calling record()).
    * Serialise access with a lock so two concurrent requests can't corrupt state.
"""
from __future__ import annotations

import logging
import threading
from typing import Optional

from hardware import GPIO
from hardware.stepper import Stepper
from hardware.claw import Claw
from config import (
    SHOULDER_PINS, ELBOW_PINS, BASE_PINS,
    SPEED_MIN_DELAY, SPEED_MAX_DELAY, SPEED_DEFAULT_DELAY,
)
from .motor_step import Axis, MotorStep

logger = logging.getLogger(__name__)


class MotionService:
    """High-level control for the robotic arm."""

    def __init__(self) -> None:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # Per-half-step delay in seconds. Smaller = faster. Accessed by every
        # Stepper via a provider callable, so changing it here is picked up
        # live by any movement currently in progress.
        self._step_delay: float = SPEED_DEFAULT_DELAY

        self._shoulder = Stepper(SHOULDER_PINS, self._get_delay, name="shoulder")
        self._elbow = Stepper(ELBOW_PINS, self._get_delay, name="elbow")
        self._base = Stepper(BASE_PINS, self._get_delay, name="base")
        self._claw = Claw()

        self._stop_event = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self._recording: list[MotorStep] = []
        self._is_recording: bool = False
        self._last_action: Optional[str] = None

    def _get_delay(self) -> float:
        return self._step_delay

    # ------------------------------------------------------------------
    # Public state helpers
    # ------------------------------------------------------------------
    @property
    def is_running(self) -> bool:
        return self._worker is not None and self._worker.is_alive()

    def status(self) -> dict:
        return {
            "running": self.is_running,
            "recorded_steps": len(self._recording),
            "recording": self._is_recording,
            "last_action": self._last_action,
            "claw_angle": self._claw.angle,
            "speed": self._delay_to_speed(self._step_delay),
        }

    # ------------------------------------------------------------------
    # Speed control
    # ------------------------------------------------------------------
    @staticmethod
    def _speed_to_delay(speed: float) -> float:
        """Map a 1..10 speed slider value to a half-step delay in seconds."""
        s = max(1.0, min(10.0, float(speed)))
        # Invert so 10 = fastest (= smallest delay), 1 = slowest.
        t = (s - 1.0) / 9.0  # 0.0 at slow, 1.0 at fast
        return SPEED_MAX_DELAY - t * (SPEED_MAX_DELAY - SPEED_MIN_DELAY)

    @staticmethod
    def _delay_to_speed(delay: float) -> float:
        t = (SPEED_MAX_DELAY - delay) / (SPEED_MAX_DELAY - SPEED_MIN_DELAY)
        t = max(0.0, min(1.0, t))
        return round(1.0 + t * 9.0, 1)

    def set_speed(self, speed: float) -> None:
        """Set the motor speed (1 = slowest, 10 = fastest). Live during motion."""
        self._step_delay = self._speed_to_delay(speed)
        logger.info("Speed set to %.1f (delay=%.4fs)", speed, self._step_delay)

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------
    def move(self, axis: Axis, steps: int) -> bool:
        """Request a fixed-size movement. Returns False if a move is already running."""
        with self._lock:
            if self.is_running:
                logger.debug("Rejecting %s/%d: motor already busy", axis, steps)
                return False
            self._stop_event.clear()
            self._worker = threading.Thread(
                target=self._run_move,
                args=(axis, steps),
                daemon=True,
                name=f"move-{axis}",
            )
            self._worker.start()
            return True

    def move_continuous(self, axis: Axis) -> bool:
        """Start stepping continuously until stop() is called.

        Used for hold-to-move: the UI calls this on button-down and stop()
        on button-up, giving smooth uninterrupted motion while held.
        """
        with self._lock:
            if self.is_running:
                return False
            self._stop_event.clear()
            self._worker = threading.Thread(
                target=self._run_continuous,
                args=(axis,),
                daemon=True,
                name=f"move-continuous-{axis}",
            )
            self._worker.start()
            return True

    def set_claw(self, angle: float) -> None:
        """Set the claw angle (0..180°). Runs synchronously — it's fast enough."""
        self._claw.set_angle(angle)
        self._last_action = f"claw={angle:.0f}°"
        if self._is_recording:
            self._recording.append(MotorStep(axis="claw", value=int(angle)))

    def stop(self) -> None:
        """Interrupt any currently running stepper movement."""
        self._stop_event.set()
        logger.info("Stop requested")

    # ------------------------------------------------------------------
    # Recording  (start/stop/replay — only the most recent recording is kept)
    # ------------------------------------------------------------------
    def start_recording(self) -> None:
        """Start a fresh recording. Discards any previously recorded steps."""
        self._recording.clear()
        self._is_recording = True
        self._last_action = "recording…"
        logger.info("Recording started")

    def stop_recording(self) -> None:
        """Stop recording. The captured steps remain available for replay."""
        self._is_recording = False
        self._last_action = f"recorded {len(self._recording)} steps"
        logger.info("Recording stopped (%d steps captured)", len(self._recording))

    def replay_recording(self) -> bool:
        """Replay the most recent recording on a background thread."""
        with self._lock:
            if self.is_running:
                return False
            if not self._recording:
                return False
            # Replay should never record itself.
            self._is_recording = False
            self._stop_event.clear()
            self._worker = threading.Thread(
                target=self._run_replay,
                daemon=True,
                name="replay",
            )
            self._worker.start()
            return True

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------
    def shutdown(self) -> None:
        self.stop()
        if self._worker is not None:
            self._worker.join(timeout=2.0)
        self._claw.shutdown()
        GPIO.cleanup()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    _AXIS_MAP = {
        # axis -> (stepper attribute name, forward flag)
        "up": ("_shoulder", True),
        "down": ("_shoulder", False),
        "forward": ("_elbow", True),
        "backward": ("_elbow", False),
        "rotate_cw": ("_base", True),
        "rotate_ccw": ("_base", False),
    }

    def _run_move(self, axis: Axis, steps: int) -> None:
        try:
            mapping = self._AXIS_MAP.get(axis)
            if mapping is None:
                logger.warning("Unknown axis for stepper move: %s", axis)
                return
            attr, forward = mapping
            stepper: Stepper = getattr(self, attr)
            executed = stepper.step(steps, forward, self._stop_event)
            stepper.release()
            self._last_action = f"{axis} x{executed}"
            if self._is_recording and executed > 0:
                self._recording.append(MotorStep(axis=axis, value=executed))
        except Exception:
            logger.exception("Movement failed")

    def _run_continuous(self, axis: Axis) -> None:
        """Step in a tight loop until stop_event fires.

        Batches are kept small (20 units) so stop response stays fast —
        the stop_event is checked between batches and inside the stepper.
        Because stepper.step() no longer releases unless interrupted, the
        coils stay energised across batches, giving smooth motion.
        """
        try:
            mapping = self._AXIS_MAP.get(axis)
            if mapping is None:
                return
            attr, forward = mapping
            stepper: Stepper = getattr(self, attr)

            total = 0
            while not self._stop_event.is_set():
                executed = stepper.step(20, forward, self._stop_event)
                total += executed
                if executed < 20:
                    break  # stop fired mid-batch; stepper already released

            # Make sure coils are released when the gesture ends.
            stepper.release()
            self._last_action = f"{axis} x{total}"
            if self._is_recording and total > 0:
                self._recording.append(MotorStep(axis=axis, value=total))
        except Exception:
            logger.exception("Continuous move failed")

    def _run_replay(self) -> None:
        logger.info("Replaying %d recorded steps", len(self._recording))
        for step in list(self._recording):
            if self._stop_event.is_set():
                break
            if step.axis == "claw":
                self._claw.set_angle(float(step.value))
                self._last_action = f"replay claw={step.value}°"
                continue
            mapping = self._AXIS_MAP.get(step.axis)
            if mapping is None:
                continue
            attr, forward = mapping
            stepper: Stepper = getattr(self, attr)
            stepper.step(step.value, forward, self._stop_event)
            stepper.release()
            self._last_action = f"replay {step.axis} x{step.value}"
        logger.info("Replay finished")
