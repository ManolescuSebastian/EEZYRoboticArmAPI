"""Central configuration for the robotic arm.

All hardware pin assignments, motion parameters, and server settings live here
so you can tune the arm without hunting through the rest of the codebase.
"""

# -------- Server --------
HOST: str = "0.0.0.0"  # listen on all interfaces
PORT: int = 5050
DEBUG: bool = False  # keep False in production; Flask reloader re-inits GPIO


# -------- GPIO pin assignments (BCM numbering) --------
# ULN2003 driver boards, each driving a 28BYJ-48 stepper (IN1..IN4).
SHOULDER_PINS: tuple[int, int, int, int] = (21, 20, 16, 12)  # up / down
ELBOW_PINS: tuple[int, int, int, int] = (26, 19, 13, 6)      # forward / backward
BASE_PINS: tuple[int, int, int, int] = (5, 22, 27, 18)       # rotate CW / CCW

CLAW_SERVO_PIN: int = 17
CLAW_PWM_FREQ_HZ: int = 50


# -------- Motion tuning --------
# Delay between individual half-steps. Smaller = faster, but too small
# causes the stepper to stall. 0.001s (1 ms) is the proven value from the
# original project.
STEP_DELAY_SEC: float = 0.001

# How many half-steps the API fires per "step" unit requested by the client.
# One 28BYJ-48 full rotation is 4096 half-steps.
HALF_STEPS_PER_UNIT: int = 8

# Claw angle range in degrees.
CLAW_MIN_ANGLE: float = 0.0
CLAW_MAX_ANGLE: float = 180.0


# -------- Hold-to-move defaults (informational; the client drives cadence) --------
# The web UI fires small movements repeatedly while a button is held. These
# values are a reasonable default; tune in static/app.js.
DEFAULT_HOLD_STEPS: int = 5
DEFAULT_HOLD_INTERVAL_MS: int = 100
