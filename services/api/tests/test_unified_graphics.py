from unittest.mock import patch
import pytest
import xarray as xr

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
    # Mock the get_diagnostics() function so we can return test data
    with patch("unified_graphics.diag.get_diagnostics") as get_diagnostics_mock:
        ds = xr.Dataset({"Obs_Minus_Forecast_adjusted": [-1, 1, 1, 2, 3]})
        get_diagnostics_mock.return_value = (ds, ds)
        response = client.get("/diag/temperature/")

    assert response.json == {
        "guess": {
            "bins": [
                {"lower": -1, "upper": 0, "value": 1},
                {"lower": 0, "upper": 1, "value": 0},
                {"lower": 1, "upper": 2, "value": 2},
                {"lower": 2, "upper": 3, "value": 2},
            ],
            "observations": 5,
            "std": 1.32664991614216,
            "mean": 1.2,
        },
        "analysis": {
            "bins": [
                {"lower": -1, "upper": 0, "value": 1},
                {"lower": 0, "upper": 1, "value": 0},
                {"lower": 1, "upper": 2, "value": 2},
                {"lower": 2, "upper": 3, "value": 2},
            ],
            "observations": 5,
            "std": 1.32664991614216,
            "mean": 1.2,
        },
    }
