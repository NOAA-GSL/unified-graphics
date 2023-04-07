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
        "dist_url": {
            "anl": "",
            "ges": "",
        },
        "map_url": {
            "anl": "",
            "ges": "",
        },
    }

    # True if any of the listed parameters are not supplied in the query string. Without
    # all of these parameters, we are unable to show any data.
    query = request.args.copy()
    model_meta = {}
    for param in [
        "model",
        "system",
        "domain",
        "background",
        "frequency",
        "initialization_time",
        "variable",
    ]:
        if param not in query:
            show_dialog = True
            continue

        model_meta[param] = query.pop(param)

    has_filters = len(query) > 0

    if not show_dialog:
        # For the wind variable, we have to use the /magnitude endpoint because it's a
        # vector. For everything else, we can use the same URL as the distribution
        # displays.
        map_endpoint = (
            ".magnitude" if request.args["variable"] == "uv" else ".diagnostics"
        )
        context["dist_url"]["anl"] = url_for(
            ".diagnostics", **model_meta, **query.to_dict(False), loop="anl"
        )
        context["dist_url"]["ges"] = url_for(
            ".diagnostics", **model_meta, **query.to_dict(False), loop="ges"
        )
        context["map_url"]["anl"] = url_for(
            map_endpoint, **model_meta, **query.to_dict(False), loop="anl"
        )
        context["map_url"]["ges"] = url_for(
            map_endpoint, **model_meta, **query.to_dict(False), loop="ges"
        )

        # Page title for the <title> tag
        context["title"] = (
            f"{request.args['variable']} "
            f"({request.args['model']} {request.args['initialization_time']}) - "
        )

    if "variable" in request.args:
        context["variable"] = diag.Variable(request.args["variable"]).name.lower()

    return stream_template(
        "layouts/diag.html",
        form=request.args,
        show_dialog=show_dialog,
        has_filters=has_filters,
        **context,
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
