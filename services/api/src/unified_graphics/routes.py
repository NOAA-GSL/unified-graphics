from flask import Blueprint, jsonify, url_for

from unified_graphics import diag

bp = Blueprint("api", __name__)


@bp.errorhandler(FileNotFoundError)
def handle_diag_file_not_found(e):
    return jsonify(msg="Diagnostic file not found"), 404


@bp.errorhandler(ValueError)
def handle_diag_file_read_error(e):
    return jsonify(msg="Unable to read diagnostic file"), 500


@bp.route("/")
def index():
    return jsonify({"diagnostics": url_for(".list_variables")})


@bp.route("/diag/")
def list_variables():
    variables = [v.name.lower() for v in diag.Variable]

    return jsonify({v: url_for(".diagnostics", variable=v) for v in variables})


@bp.route("/diag/<variable>/")
def diagnostics(variable):
    if not hasattr(diag, variable):
        return jsonify(msg=f"Variable not found: '{variable}'"), 404

    variable_diagnostics = getattr(diag, variable)
    data = variable_diagnostics()

    response = jsonify(
        {"type": "FeatureCollection", "features": [obs.to_geojson() for obs in data]}
    )

    return response
