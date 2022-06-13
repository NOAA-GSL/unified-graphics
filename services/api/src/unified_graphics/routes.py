from flask import Blueprint, current_app, jsonify

from unified_graphics import diag


bp = Blueprint("api", __name__)


@bp.route("/")
def index():
    current_app.logger.info("index()")
    return jsonify({"msg": "Hello, Dave"})


@bp.route("/diag/temperature/")
def diag_temperature():
    current_app.logger.info("diag_temperature()")

    diag.get_diagnostics()

    return jsonify(
        {
            "background": {
                "bins": [],
                "observations": 0,
                "std": 0,
                "mean": 0,
            },
            "analysis": {
                "bins": [],
                "observations": 0,
                "std": 0,
                "mean": 0,
            },
        }
    )
