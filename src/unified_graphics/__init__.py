from logging.config import dictConfig
from typing import Any, Mapping, Optional

from flask import Flask

from . import models, routes

__version__ = "0.1.0"


def create_app(config: Optional[Mapping[str, Any]] = None):
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
    app.config.from_mapping(config)

    if app.debug and app.config.get("PROFILE", "False") == "True":
        from werkzeug.middleware.profiler import ProfilerMiddleware

        app.wsgi_app = ProfilerMiddleware(  # type: ignore
            app.wsgi_app,
            restrictions=[30],
            stream=None,  # Disable stdout
            profile_dir="tmp/profiler",
            filename_format="{method}-{path}-{time:.0f}-{elapsed:.0f}ms.prof",
        )

    models.db.init_app(app)

    app.register_blueprint(routes.bp)

    return app
