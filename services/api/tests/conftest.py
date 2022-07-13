import pytest

from unified_graphics import create_app


@pytest.fixture
def app(tmp_path):
    app = create_app()
    app.config["DIAG_DIR"] = str(tmp_path / "data")

    yield app


@pytest.fixture
def client(app):
    return app.test_client()
