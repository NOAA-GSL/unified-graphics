from flask import Blueprint, jsonify, url_for

from unified_graphics import diag

bp = Blueprint("api", __name__)


# TODO: Don't hardcode the error message
# Instead of hard-coding the error message, we should read e.args[0] to allow different
# types of 404s, such as a missing variable, init time, or zarr
@bp.errorhandler(FileNotFoundError)
def handle_diag_file_not_found(e):
    return jsonify(msg="Diagnostic file not found"), 404


# TODO: Don't hardcode the error message
# Instead of hard-coding the error message, we should read e.args[0] to allow different
# types of 500s, such as an unknown variable
@bp.errorhandler(ValueError)
def handle_diag_file_read_error(e):
    # FIXME: Some ValueErrors should be 400s
    return jsonify(msg="Unable to read diagnostic file"), 500


@bp.route("/")
def index():
    return jsonify({"diagnostics": url_for(".list_variables")})


@bp.route("/diag/")
def list_variables():
    variables = [v.name.lower() for v in diag.Variable]

    return jsonify({v: url_for(".list_model_runs", variable=v) for v in variables})


@bp.route("/diag/<variable>/")
def list_model_runs(variable):
    if not hasattr(diag, variable):
        return jsonify(msg=f"Variable not found: '{variable}'"), 404

    init_times = diag.initialization_times(variable)

    return jsonify(
        {
            t: url_for(".diagnostics", variable=variable, initialization_time=t)
            for t in init_times
        }
    )


# BUG: No trailing slash
@bp.route("/diag/<variable>/<initialization_time>")
def diagnostics(variable, initialization_time):
    if not hasattr(diag, variable):
        return jsonify(msg=f"Variable not found: '{variable}'"), 404

    variable_diagnostics = getattr(diag, variable)
    data = variable_diagnostics(initialization_time)

    response = jsonify(
        {"type": "FeatureCollection", "features": [obs.to_geojson() for obs in data]}
    )

    return response
