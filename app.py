"""Flask entry point for the EEZY Robotic Arm API.

Run with:
    python app.py

The web UI is at http://<pi-ip>:5050/
API routes live under /api — see api/routes.py.
"""
from __future__ import annotations

import atexit
import logging

from flask import Flask

from api.routes import api_bp, page_bp, get_service
from config import DEBUG, HOST, PORT


def create_app() -> Flask:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )

    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.register_blueprint(page_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Make sure the service is created up front (and GPIO initialised)
    # so the first request isn't surprised by hardware init latency.
    get_service()

    atexit.register(lambda: get_service().shutdown())
    return app


if __name__ == "__main__":
    create_app().run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
        threaded=True,
        use_reloader=False,  # reloader re-inits GPIO — bad.
    )
