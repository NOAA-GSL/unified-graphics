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
    response = client.get("/diag/temperature/")

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
