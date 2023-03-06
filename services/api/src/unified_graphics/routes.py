from flask import (
    Blueprint,
    jsonify,
    make_response,
    redirect,
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
    variables = [v for v in diag.Variable]
    should_redirect = False

    if "variable" in request.args:
        variable = diag.Variable(request.args["variable"])
    else:
        variable = variables[0]
        should_redirect = True

    init_times = list(diag.initialization_times(variable.name.lower()))

    if "initialization_time" in request.args:
        init_time = request.args["initialization_time"]
    else:
        init_time = init_times[0]
        should_redirect = True

    if should_redirect:
        return redirect(
            url_for(".index", variable=variable.value, initialization_time=init_time)
        )

    return stream_template(
        "layouts/diag.html",
        variables=variables,
        initialization_times=init_times,
        form={
            "variable": variable,
            "initialization_time": init_time,
            "is_used": request.args.get("is_used", "off") == "on",
        },
    )


@bp.route("/serviceworker.js")
def serviceworker():
    return make_response(send_from_directory("static", path="serviceworker.js"))


@bp.route("/diag/")
def list_variables():
    variables = [v.name.lower() for v in diag.Variable]

    return jsonify(
        [
            {
                "name": v,
                "url": url_for(".list_model_runs", variable=v),
                # FIXME: We need to be able to look up variable types
                "type": "vector" if v == "wind" else "scalar",
            }
            for v in variables
        ]
    )


@bp.route("/diag/<variable>/")
def list_model_runs(variable):
    if not hasattr(diag, variable):
        return jsonify(msg=f"Variable not found: '{variable}'"), 404

    init_times = diag.initialization_times(variable)

    return jsonify(
        {
            t: url_for(".list_loops", variable=variable, initialization_time=t)
            for t in init_times
        }
    )


@bp.route("/diag/<variable>/<initialization_time>/")
def list_loops(variable, initialization_time):
    loops = diag.loops(variable, initialization_time)

    return jsonify(
        {
            loop: url_for(
                ".diagnostics",
                variable=variable,
                initialization_time=initialization_time,
                loop=loop,
            )
            for loop in loops
        }
    )


@bp.route("/diag/<variable>/<initialization_time>/<loop>/")
def diagnostics(variable, initialization_time, loop):
    if not hasattr(diag, variable):
        return jsonify(msg=f"Variable not found: '{variable}'"), 404

    variable_diagnostics = getattr(diag, variable)
    data = variable_diagnostics(initialization_time, diag.MinimLoop(loop), request.args)

    response = jsonify(
        {"type": "FeatureCollection", "features": [obs.to_geojson() for obs in data]}
    )

    return response
