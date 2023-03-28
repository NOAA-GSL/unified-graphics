from flask import (
    Blueprint,
    jsonify,
    make_response,
    request,
    send_from_directory,
    stream_template,
    url_for,
)

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
    show_dialog = False
    context = {
        "model_metadata": diag.get_model_metadata(),
        "data_url": {
            "anl": "",
            "ges": "",
        },
    }

    # True if any of the listed parameters are not supplied in the query string. Without
    # all of these parameters, we are unable to show any data.
    show_dialog = any(
        param not in request.args
        for param in [
            "model",
            "system",
            "domain",
            "background",
            "frequency",
            "initialization_time",
            "variable",
        ]
    )

    if not show_dialog:
        context["data_url"]["anl"] = url_for(".diagnostics", **request.args, loop="anl")
        context["data_url"]["ges"] = url_for(".diagnostics", **request.args, loop="ges")

    return stream_template(
        "layouts/diag.html", form=request.args, show_dialog=show_dialog, **context
    )


@bp.route("/serviceworker.js")
def serviceworker():
    return make_response(send_from_directory("static", path="serviceworker.js"))


@bp.route(
    "/diag/<model>/<system>/<domain>/<background>/<frequency>"
    "/<variable>/<initialization_time>/<loop>/"
)
def diagnostics(
    model, system, domain, background, frequency, variable, initialization_time, loop
):
    try:
        v = diag.Variable(variable)
    except ValueError:
        return jsonify(msg=f"Variable not found: '{variable}'"), 404

    variable_diagnostics = getattr(diag, v.name.lower())
    data = variable_diagnostics(
        model,
        system,
        domain,
        background,
        frequency,
        initialization_time,
        diag.MinimLoop(loop),
        request.args,
    )

    response = jsonify(
        {"type": "FeatureCollection", "features": [obs.to_geojson() for obs in data]}
    )

    return response


@bp.route(
    "/diag/<model>/<system>/<domain>/<background>/<frequency>"
    "/<variable>/<initialization_time>/<loop>/magnitude/"
)
def magnitude(
    model, system, domain, background, frequency, variable, initialization_time, loop
):
    try:
        v = diag.Variable(variable)
    except ValueError:
        return jsonify(msg=f"Variable not found: '{variable}'"), 404

    variable_diagnostics = getattr(diag, v.name.lower())
    data = variable_diagnostics(
        model,
        system,
        domain,
        background,
        frequency,
        initialization_time,
        diag.MinimLoop(loop),
        request.args,
    )
    data = diag.magnitude(data)

    response = jsonify(
        {"type": "FeatureCollection", "features": [obs.to_geojson() for obs in data]}
    )

    return response
