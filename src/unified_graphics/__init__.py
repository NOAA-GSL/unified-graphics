from logging.config import dictConfig

from flask import Flask

__version__ = "0.1.0"


def cors(response):
    """Add CORS header for frontend development"""
    response.access_control_allow_origin = "http://localhost:3000"
    return response


def create_app(config=None):
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                },
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://flask.logging.wsgi_errors_stream",
                    "formatter": "default",
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["wsgi"],
            },
        }
    )

    app = Flask(__name__)
    app.config.from_prefixed_env()

    if app.config.get("ENV", "production") == "development":
        app.after_request(cors)

    from . import routes

    app.register_blueprint(routes.bp)

    return app
