from dataclasses import asdict

from flask import Blueprint, current_app, jsonify

from unified_graphics import diag


bp = Blueprint("api", __name__)


@bp.route("/")
def index():
    current_app.logger.info("index()")
    return jsonify({"msg": "Hello, Dave"})


@bp.route("/diag/temperature/")
def diag_temperature():
    guess = diag.get_diagnostics(diag.MinimLoop.GUESS)
    analysis = diag.get_diagnostics(diag.MinimLoop.ANALYSIS)
    return jsonify(guess=guess, analysis=analysis)


@bp.route("/diag/wind/")
def diag_wind():
    guess = diag.wind(diag.MinimLoop.GUESS)
    analysis = diag.wind(diag.MinimLoop.ANALYSIS)
    return jsonify(guess=asdict(guess), analysis=asdict(analysis))
