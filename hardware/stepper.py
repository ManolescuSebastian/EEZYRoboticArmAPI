"""Driver for a single 28BYJ-48 stepper connected via a ULN2003 board.

One Stepper instance owns one motor's four GPIO pins. Movement is interruptible
via a threading.Event, so the control layer can issue a stop at any time.
"""
from __future__ import annotations

import logging
import threading
from time import sleep

from . import GPIO
from config import STEP_DELAY_SEC, HALF_STEPS_PER_UNIT

logger = logging.getLogger(__name__)

# Standard 8-phase half-step sequence for the 28BYJ-48 stepper.
HALF_STEP_SEQUENCE: tuple[tuple[int, int, int, int], ...] = (
    (1, 0, 0, 1),
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
)


class Stepper:
    """Drives one stepper motor through four GPIO pins (IN1..IN4)."""

    def __init__(self, pins: tuple[int, int, int, int], name: str = "stepper") -> None:
        self.pins = pins
        self.name = name
        self._configure_pins()

    def __repr__(self) -> str:
        return f"Stepper(name={self.name!r}, pins={self.pins})"

    def _configure_pins(self) -> None:
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, False)

    def release(self) -> None:
        """Drop all pins LOW so the coils aren't energised (saves power/heat)."""
        for pin in self.pins:
            GPIO.output(pin, False)

    def step(self, units: int, forward: bool, stop_event: threading.Event) -> int:
        """Step the motor `units` units in a given direction.

        One unit = HALF_STEPS_PER_UNIT half-steps. Returns the number of units
        actually executed (fewer than requested if the stop_event fires).
        """
        sequence = HALF_STEP_SEQUENCE if forward else tuple(reversed(HALF_STEP_SEQUENCE))
        executed = 0

        for _ in range(units):
            if stop_event.is_set():
                logger.debug("%s: stop requested after %d/%d units", self.name, executed, units)
                break
            for phase in sequence:
                for pin_index, pin in enumerate(self.pins):
                    GPIO.output(pin, phase[pin_index])
                    sleep(STEP_DELAY_SEC)
            executed += 1

        self.release()
        return executed
