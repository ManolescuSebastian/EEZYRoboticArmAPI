"""Claw servo driver.

The claw is a hobby servo driven by hardware PWM. Angles are expressed in
degrees (0–180); internally they're converted to a PWM duty-cycle percentage.
"""
from __future__ import annotations

import logging
from time import sleep

from . import GPIO
from config import (
    CLAW_SERVO_PIN,
    CLAW_PWM_FREQ_HZ,
    CLAW_MIN_ANGLE,
    CLAW_MAX_ANGLE,
)

logger = logging.getLogger(__name__)


class Claw:
    """Positional control for the claw servo."""

    def __init__(self) -> None:
        GPIO.setup(CLAW_SERVO_PIN, GPIO.OUT)
        self._pwm = GPIO.PWM(CLAW_SERVO_PIN, CLAW_PWM_FREQ_HZ)
        self._pwm.start(0)
        self._current_angle: float = CLAW_MIN_ANGLE

    def __repr__(self) -> str:
        return f"Claw(pin={CLAW_SERVO_PIN}, angle={self._current_angle:.1f})"

    @property
    def angle(self) -> float:
        return self._current_angle

    @staticmethod
    def _angle_to_duty(angle: float) -> float:
        """Map 0..180° to a servo-friendly duty cycle (~2% .. 12%)."""
        clamped = max(CLAW_MIN_ANGLE, min(CLAW_MAX_ANGLE, angle))
        return 2.0 + (clamped / 180.0) * 10.0

    def set_angle(self, angle: float) -> None:
        """Move the claw to a given angle (0 = closed, 180 = fully open)."""
        duty = self._angle_to_duty(angle)
        self._pwm.ChangeDutyCycle(duty)
        sleep(0.3)  # give the servo time to reach position
        # Stop the pulse so the servo doesn't buzz / draw current while idle.
        self._pwm.ChangeDutyCycle(0)
        self._current_angle = max(CLAW_MIN_ANGLE, min(CLAW_MAX_ANGLE, angle))
        logger.debug("Claw set to %.1f° (duty=%.1f%%)", self._current_angle, duty)

    def shutdown(self) -> None:
        self._pwm.stop()
