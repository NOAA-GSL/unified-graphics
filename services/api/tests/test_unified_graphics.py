from unittest import mock

import pytest  # noqa: F401

from unified_graphics.diag import Bin, ScalarDiag, VectorDiag, VectorVariable


def test_root_endpoint(client):
    response = client.get("/")

    assert response.json == {"msg": "Hello, Dave"}


@mock.patch("unified_graphics.diag.temperature", autospec=True)
def test_temperature_diag(mock_diag_temperature, client):
    mock_diag_temperature.return_value = ScalarDiag(
        bins=[Bin(lower=0, upper=1, value=3), Bin(lower=1, upper=2, value=5)],
        observations=5,
        std=1.2,
        mean=4,
    )

    response = client.get("/diag/temperature/")

    assert response.status_code == 200
    assert response.json == {
        "guess": {
            "bins": [
                {"lower": 0, "upper": 1, "value": 3},
                {"lower": 1, "upper": 2, "value": 5},
            ],
            "observations": 5,
            "std": 1.2,
            "mean": 4,
        },
        "analysis": {
            "bins": [
                {"lower": 0, "upper": 1, "value": 3},
                {"lower": 1, "upper": 2, "value": 5},
            ],
            "observations": 5,
            "std": 1.2,
            "mean": 4,
        },
    }


@pytest.mark.xfail
def test_temperature_diag_not_found():
    assert 0


@pytest.mark.xfail
def test_temperature_diag_read_error():
    assert 0


@mock.patch("unified_graphics.diag.wind", autospec=True)
def test_wind_diag(mock_diag_wind, client):
    mock_diag_wind.return_value = VectorDiag(
        observation=VectorVariable(direction=[], magnitude=[]),
        forecast=VectorVariable(direction=[], magnitude=[]),
    )

    response = client.get("/diag/wind/")
    assert response.status_code == 200
    assert response.json == {
        "guess": {
            "observation": {"direction": [], "magnitude": []},
            "forecast": {"direction": [], "magnitude": []},
        },
        "analysis": {
            "observation": {"direction": [], "magnitude": []},
            "forecast": {"direction": [], "magnitude": []},
        },
    }


@mock.patch("unified_graphics.diag.wind", autospec=True)
def test_wind_diag_not_found(mock_diag_wind, client):
    mock_diag_wind.side_effect = FileNotFoundError()

    response = client.get("/diag/wind/")

    assert response.status_code == 404
    assert response.json == {"msg": "Diagnostic file not found"}


@mock.patch("unified_graphics.diag.wind", autospec=True)
def test_wind_diag_read_error(mock_diag_wind, client):
    mock_diag_wind.side_effect = ValueError()

    response = client.get("/diag/wind/")

    assert response.status_code == 500
    assert response.json == {"msg": "Unable to read diagnostic file"}
