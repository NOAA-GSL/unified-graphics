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
    guess = diag.temperature(diag.MinimLoop.GUESS)
    analysis = diag.temperature(diag.MinimLoop.ANALYSIS)
    return jsonify(guess=guess, analysis=analysis)


@bp.route("/diag/wind/")
def diag_wind():
    try:
        guess = diag.wind(diag.MinimLoop.GUESS)
        analysis = diag.wind(diag.MinimLoop.ANALYSIS)

        response = jsonify(guess=asdict(guess), analysis=asdict(analysis))
    except FileNotFoundError:
        response = jsonify(msg="Diagnostic file not found")
        response.status_code = 404
    except ValueError:
        response = jsonify(msg="Unable to read diagnostic file")
        response.status_code = 500

    return response
