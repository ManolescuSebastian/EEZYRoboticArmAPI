"""Data model for a single recorded motion step."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Axis = Literal[
    "up", "down", "forward", "backward", "rotate_cw", "rotate_ccw", "claw"
]


@dataclass(frozen=True)
class MotorStep:
    """A single recorded motion.

    For stepper axes `value` is the number of units to step.
    For the claw, `value` is the target angle in degrees.
    """
    axis: Axis
    value: int

    def __repr__(self) -> str:
        return f"MotorStep(axis={self.axis!r}, value={self.value})"
