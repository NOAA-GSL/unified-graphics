import pytest

from unified_graphics import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config["DIAG_DIR"] = "/test/data/"

    yield app


@pytest.fixture
def client(app):
    return app.test_client()
