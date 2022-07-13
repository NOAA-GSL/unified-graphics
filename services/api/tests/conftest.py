import pytest

from unified_graphics import create_app


@pytest.fixture
def app(tmp_path):
    diag_dir = tmp_path / "data"
    diag_dir.mkdir()

    app = create_app()
    app.config["DIAG_DIR"] = str(diag_dir)

    yield app


@pytest.fixture
def client(app):
    return app.test_client()
