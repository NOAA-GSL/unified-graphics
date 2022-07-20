from unittest import mock

import pytest  # noqa: F401

from unified_graphics.diag import (
    Bin,
    Coordinate,
    ScalarDiag,
    VectorDiag,
    VectorVariable,
)


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


@mock.patch("unified_graphics.diag.temperature", autospec=True)
def test_temperature_diag_not_found(mock_diag_temperature, client):
    mock_diag_temperature.side_effect = FileNotFoundError()

    response = client.get("/diag/temperature/")

    assert response.status_code == 404
    assert response.json == {"msg": "Diagnostic file not found"}


@mock.patch("unified_graphics.diag.temperature", autospec=True)
def test_temperature_diag_read_error(mock_diag_temperature, client):
    mock_diag_temperature.side_effect = ValueError()

    response = client.get("/diag/temperature/")

    assert response.status_code == 500
    assert response.json == {"msg": "Unable to read diagnostic file"}


@mock.patch("unified_graphics.diag.wind", autospec=True)
def test_wind_diag(mock_diag_wind, client):
    mock_diag_wind.side_effect = [
        VectorDiag(
            observation=VectorVariable(
                direction=[0.0],
                magnitude=[2.7],
            ),
            forecast=VectorVariable(
                direction=[129.55],
                magnitude=[0.45],
            ),
            coords=[Coordinate(longitude=-123.4, latitude=37.0)],
        ),
        VectorDiag(
            observation=VectorVariable(
                direction=[10.0],
                magnitude=[27.0],
            ),
            forecast=VectorVariable(
                direction=[299.08],
                magnitude=[3.3],
            ),
            coords=[Coordinate(longitude=-80.0, latitude=31.2)],
        ),
    ]

    response = client.get("/diag/wind/")
    assert response.status_code == 200
    assert response.json == {
        "guess": {
            "observation": {
                "direction": [0.0],
                "magnitude": [2.7],
            },
            "forecast": {
                "direction": [129.55],
                "magnitude": [0.45],
            },
            "coords": [[-123.4, 37.0]],
        },
        "analysis": {
            "observation": {
                "direction": [10.0],
                "magnitude": [27.0],
            },
            "forecast": {
                "direction": [299.08],
                "magnitude": [3.3],
            },
            "coords": [[-80.0, 31.2]],
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


def test_unknown_variable(client):
    response = client.get("/diag/not_a_variable/")

    assert response.status_code == 404
    assert response.json == {"msg": "Variable not found: 'not_a_variable'"}
