import pytest

from unified_graphics import create_app


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("FLASK_DIAG_DIR", "/test/data/")

    app = create_app()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()
