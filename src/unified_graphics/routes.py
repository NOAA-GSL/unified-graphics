from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    request,
    send_from_directory,
    stream_template,
    url_for,
)
from werkzeug.datastructures import MultiDict
from zarr.errors import FSPathExistNotDir, GroupNotFoundError  # type: ignore

from unified_graphics import diag
from unified_graphics.models import db

bp = Blueprint("api", __name__)


def parse_filters(query: MultiDict) -> dict:
    def parse_value(value):
        if "::" in value:
            return [parse_value(tok) for tok in value.split("::")]

        if value in ["true", "false"]:
            return value == "true"

        try:
            return float(value)
        except ValueError:
            return value

    filters = {}
    for col, value_list in query.lists():
        val = [parse_value(val) for val in value_list]
        filters[col] = val if len(val) > 1 else val[0]

    return filters


@bp.errorhandler(GroupNotFoundError)
def handle_diag_group_not_found(e):
    current_app.logger.exception("Unable to read diagnostic group")
    if isinstance(e, FSPathExistNotDir):
        return jsonify(msg="Unable to read diagnostic file group"), 500

    return jsonify(msg="Diagnostic file group not found"), 404


# TODO: Don't hardcode the error message
# Instead of hard-coding the error message, we should read e.args[0] to allow different
# types of 404s, such as a missing variable, init time, or zarr
@bp.errorhandler(FileNotFoundError)
def handle_diag_file_not_found(e):
    current_app.logger.exception("Diagnostic file not found")
    return jsonify(msg="Diagnostic file not found"), 404


# TODO: Don't hardcode the error message
# Instead of hard-coding the error message, we should read e.args[0] to allow different
# types of 500s, such as an unknown variable
@bp.errorhandler(ValueError)
def handle_diag_file_read_error(e):
    current_app.logger.exception("Unable to read diagnostic file")
    # FIXME: Some ValueErrors should be 400s
    return jsonify(msg="Unable to read diagnostic file"), 500


@bp.route("/")
def index():
    show_dialog = False
    context = {
        "model_metadata": diag.get_model_metadata(db.session),
        "dist_url": {
            "anl": "",
            "ges": "",
        },
        "map_url": {
            "anl": "",
            "ges": "",
        },
        "history_url": {
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
        history_params = {
            k: v for k, v in model_meta.items() if k != "initialization_time"
        }
        context["history_url"]["anl"] = url_for(
            ".history", **history_params, **query.to_dict(False), loop="anl"
        )
        context["history_url"]["ges"] = url_for(
            ".history", **history_params, **query.to_dict(False), loop="ges"
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


@bp.route("/diag/<model>/<system>/<domain>/<background>/<frequency>/<variable>/<loop>/")
def history(model, system, domain, background, frequency, variable, loop):
    args = request.args.copy()
    initialization_time = datetime.fromisoformat(args.pop("initialization_time"))
    data = diag.history(
        current_app.config["DIAG_PARQUET"],
        model,
        system,
        domain,
        background,
        frequency,
        diag.Variable(variable),
        diag.MinimLoop(loop),
        initialization_time,
        args,
    )

    return data.to_json(orient="records", date_format="iso"), {
        "Content-Type": "application/json"
    }


@bp.route(
    "/diag/<model>/<system>/<domain>/<background>/<frequency>"
    "/<variable>/<initialization_time>/<loop>/"
)
def diagnostics(
    model, system, domain, background, frequency, variable, initialization_time, loop
):
    filters = parse_filters(request.args)

    data = diag.diag_observations(
        model,
        system,
        domain,
        background,
        frequency,
        variable,
        datetime.fromisoformat(initialization_time),
        loop,
        current_app.config["DIAG_PARQUET"],
        filters,
    )[
        [
            "obs_minus_forecast_adjusted",
            "obs_minus_forecast_unadjusted",
            "observation",
            "longitude",
            "latitude",
        ]
    ]

    if "component" in data.columns.names:
        data.columns = ["_".join(col) for col in data.columns]

    return data.to_json(orient="records"), {"Content-Type": "application/json"}


@bp.route(
    "/diag/<model>/<system>/<domain>/<background>/<frequency>"
    "/<variable>/<initialization_time>/<loop>/magnitude/"
)
def magnitude(
    model, system, domain, background, frequency, variable, initialization_time, loop
):
    filters = parse_filters(request.args)

    data = diag.diag_observations(
        model,
        system,
        domain,
        background,
        frequency,
        variable,
        datetime.fromisoformat(initialization_time),
        loop,
        current_app.config["DIAG_PARQUET"],
        filters,
    )[
        [
            "obs_minus_forecast_adjusted",
            "obs_minus_forecast_unadjusted",
            "observation",
            "longitude",
            "latitude",
        ]
    ]
    data = diag.magnitude(data.stack())

    return data.to_json(orient="records"), {"Content-Type": "application/json"}
