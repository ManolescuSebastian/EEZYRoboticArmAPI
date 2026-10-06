"""HTTP API for the robotic arm.

All endpoints are JSON POSTs (except /api/status and /). Request bodies are
validated minimally — this is a trusted LAN tool, not a public API.
"""
from __future__ import annotations

import logging
from typing import get_args

from flask import Blueprint, jsonify, render_template, request

from control.motion_service import MotionService
from control.motor_step import Axis
from config import CLAW_MIN_ANGLE, CLAW_MAX_ANGLE

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)
page_bp = Blueprint("page", __name__)

# Module-level singleton. Instantiated lazily so `import` doesn't touch GPIO.
_service: MotionService | None = None


def get_service() -> MotionService:
    global _service
    if _service is None:
        _service = MotionService()
    return _service


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------
@page_bp.route("/")
def index():
    return render_template("index.html")


# ----------------------------------------------------------------------
# API
# ----------------------------------------------------------------------
_STEPPER_AXES = {"up", "down", "forward", "backward", "rotate_cw", "rotate_ccw"}
_ALL_AXES = set(get_args(Axis))


@api_bp.route("/status", methods=["GET"])
def status():
    return jsonify(get_service().status())


@api_bp.route("/move", methods=["POST"])
def move():
    body = request.get_json(silent=True) or {}
    axis = body.get("axis")
    steps = body.get("steps")

    if axis not in _STEPPER_AXES:
        return jsonify(error=f"invalid axis '{axis}'"), 400
    if not isinstance(steps, int) or steps <= 0:
        return jsonify(error="'steps' must be a positive integer"), 400

    accepted = get_service().move(axis, steps)
    if not accepted:
        return jsonify(error="busy"), 409
    return jsonify(ok=True, axis=axis, steps=steps)


@api_bp.route("/move_start", methods=["POST"])
def move_start():
    """Begin continuous movement on an axis. Call /stop to end it."""
    body = request.get_json(silent=True) or {}
    axis = body.get("axis")
    if axis not in _STEPPER_AXES:
        return jsonify(error=f"invalid axis '{axis}'"), 400
    accepted = get_service().move_continuous(axis)
    if not accepted:
        return jsonify(error="busy"), 409
    return jsonify(ok=True, axis=axis)


@api_bp.route("/claw", methods=["POST"])
def claw():
    body = request.get_json(silent=True) or {}
    angle = body.get("angle")
    if not isinstance(angle, (int, float)):
        return jsonify(error="'angle' must be a number"), 400
    if not CLAW_MIN_ANGLE <= angle <= CLAW_MAX_ANGLE:
        return jsonify(
            error=f"'angle' must be between {CLAW_MIN_ANGLE} and {CLAW_MAX_ANGLE}"
        ), 400

    get_service().set_claw(float(angle))
    return jsonify(ok=True, angle=angle)


@api_bp.route("/stop", methods=["POST"])
def stop():
    get_service().stop()
    return jsonify(ok=True)


@api_bp.route("/speed", methods=["POST"])
def speed():
    """Set the global motor speed. Takes effect live (mid-movement)."""
    body = request.get_json(silent=True) or {}
    value = body.get("value")
    if not isinstance(value, (int, float)):
        return jsonify(error="'value' must be a number"), 400
    if not 1.0 <= value <= 10.0:
        return jsonify(error="'value' must be between 1 and 10"), 400
    get_service().set_speed(float(value))
    return jsonify(ok=True, value=value)


@api_bp.route("/recording/start", methods=["POST"])
def start_recording():
    """Begin a new recording. Discards any previously captured steps."""
    get_service().start_recording()
    return jsonify(ok=True)


@api_bp.route("/recording/stop", methods=["POST"])
def stop_recording():
    """Stop recording. The captured steps remain available for replay."""
    get_service().stop_recording()
    return jsonify(ok=True)


@api_bp.route("/recording/replay", methods=["POST"])
def replay_recording():
    started = get_service().replay_recording()
    if not started:
        return jsonify(error="nothing to replay or busy"), 409
    return jsonify(ok=True)
