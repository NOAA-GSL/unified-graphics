from flask import Blueprint, current_app, jsonify
import numpy as np

from unified_graphics import diag


bp = Blueprint("api", __name__)


@bp.route("/")
def index():
    current_app.logger.info("index()")
    return jsonify({"msg": "Hello, Dave"})


@bp.route("/diag/temperature/")
def diag_temperature():
    def histogram(data):
        counts, bins = np.histogram(data, bins="auto")
        for idx, count in enumerate(counts):
            yield {"lower": bins[idx], "upper": bins[idx + 1], "value": int(count)}

    current_app.logger.info("diag_temperature()")

    guess, analysis = diag.get_diagnostics()

    guess_diag = {
        "bins": list(histogram(guess["Obs_Minus_Forecast_adjusted"].values)),
        "observations": len(guess["Obs_Minus_Forecast_adjusted"]),
        "std": np.std(guess["Obs_Minus_Forecast_adjusted"].values),
        "mean": np.mean(guess["Obs_Minus_Forecast_adjusted"].values),
    }

    analysis_diag = {
        "bins": list(histogram(analysis["Obs_Minus_Forecast_adjusted"].values)),
        "observations": len(analysis["Obs_Minus_Forecast_adjusted"]),
        "std": np.std(analysis["Obs_Minus_Forecast_adjusted"].values),
        "mean": np.mean(analysis["Obs_Minus_Forecast_adjusted"].values),
    }

    return jsonify(guess=guess_diag, analysis=analysis_diag)
