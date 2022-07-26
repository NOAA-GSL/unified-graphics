from flask import Blueprint, current_app, jsonify

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
    current_app.logger.info("index()")
    return jsonify({"msg": "Hello, Dave"})


@bp.route("/diag/wind/<loop>/<value_type>/")
def wind(loop, value_type):
    try:
        loop_enum = diag.MinimLoop(loop)
        type_enum = diag.ValueType(value_type)
    except ValueError:
        raise FileNotFoundError()

    return jsonify(diag.wind(loop_enum, type_enum))


@bp.route("/diag/<variable>/")
def diagnostics(variable):
    if not hasattr(diag, variable):
        return jsonify(msg=f"Variable not found: '{variable}'"), 404

    variable_diagnostics = getattr(diag, variable)

    guess = variable_diagnostics(diag.MinimLoop.GUESS)
    analysis = variable_diagnostics(diag.MinimLoop.ANALYSIS)

    return jsonify(guess=guess, analysis=analysis)
