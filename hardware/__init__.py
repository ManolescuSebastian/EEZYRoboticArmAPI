"""Hardware abstraction layer.

Attempts to import the real RPi.GPIO library. If that fails (e.g. running on a
dev machine or a Pi 5 without the legacy library), fall back to rpi-lgpio which
is API-compatible. If neither is available, a no-op mock is used so the rest of
the code can at least be imported and the Flask server will start — useful for
UI work.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO  # type: ignore
    logger.info("Using RPi.GPIO")
except (ImportError, RuntimeError):
    try:
        import rpi_lgpio as GPIO  # type: ignore
        logger.info("Using rpi-lgpio (Pi 5 compatible)")
    except ImportError:
        logger.warning(
            "No GPIO library available — running with a mock. "
            "The arm will not actually move."
        )

        class _MockGPIO:
            BCM = "BCM"
            OUT = "OUT"

            def setmode(self, *_): pass
            def setwarnings(self, *_): pass
            def setup(self, *_, **__): pass
            def output(self, *_): pass
            def cleanup(self, *_): pass

            class PWM:
                def __init__(self, *_): pass
                def start(self, *_): pass
                def stop(self, *_): pass
                def ChangeDutyCycle(self, *_): pass

        GPIO = _MockGPIO()  # type: ignore

__all__ = ["GPIO"]
