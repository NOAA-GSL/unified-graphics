from flask import (
    Blueprint,
    jsonify,
    make_response,
    request,
    send_from_directory,
    stream_template,
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
    context = {}

    # Contains the values supplied by the query parameters in the request that
    # are used to load the data.
    form = {}

    for param in [
        "model",
        "system",
        "domain",
        "frequency",
        "initialization_time",
        "variable",
    ]:
        collection_name = f"{param}_list"
        collection = getattr(diag, f"get_{collection_name}")(**form)
        form[collection_name] = collection

        if param in request.args:
            form[param] = request.args[param]
        else:
            # Because these values are hierarchical, we can't build a set of
            # options for one if its parent value isn't specified. This means
            # that if someone sets ?model=RTMA&domain=CONUS, only the model
            # select will be populated, because we have no way of knowing if
            # their domain selection is valid for that model. Therefore, we stop
            # processing the parameters as soon as we find one that is missing.
            show_dialog = True
            break

    return stream_template(
        "layouts/diag.html", form=form, show_dialog=show_dialog, **context
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
    print(variable)
    if not hasattr(diag, variable):
        return jsonify(msg=f"Variable not found: '{variable}'"), 404

    variable_diagnostics = getattr(diag, variable)
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
