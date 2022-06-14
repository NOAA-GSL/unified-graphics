from flask import Blueprint, current_app, jsonify

from unified_graphics import diag


bp = Blueprint("api", __name__)


@bp.route("/")
def index():
    current_app.logger.info("index()")
    return jsonify({"msg": "Hello, Dave"})


@bp.route("/diag/temperature/")
def diag_temperature():
    guess = diag.get_diagnostics()
    analysis = diag.get_diagnostics()
    return jsonify(guess=guess, analysis=analysis)
