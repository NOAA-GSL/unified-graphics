from unittest.mock import patch
import pytest

from unified_graphics import create_app


@pytest.fixture()
def app():
    app = create_app()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_root_endpoint(client):
    response = client.get("/")

    assert response.json == {"msg": "Hello, Dave"}


def test_temperature_diag_distribution(client):
    with patch("unified_graphics.diag.get_diagnostics") as get_diagnostics_mock:
        response = client.get("/diag/temperature/")

    assert get_diagnostics_mock.called
    assert response.json == {
        "background": {
            "bins": [],
            "observations": 0,
            "std": 0,
            "mean": 0,
        },
        "analysis": {
            "bins": [],
            "observations": 0,
            "std": 0,
            "mean": 0,
        },
    }
