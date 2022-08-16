from unittest import mock

import pytest  # noqa: F401

from unified_graphics.diag import (
    Coordinate,
    MinimLoop,
    PolarCoordinate,
    VectorObservation,
)


def test_root_endpoint(client):
    response = client.get("/")

    assert response.json == {"msg": "Hello, Dave"}


@mock.patch("unified_graphics.diag.temperature", autospec=True)
@pytest.mark.parametrize(
    "loop,expected", [("ges", [MinimLoop.GUESS]), ("anl", [MinimLoop.ANALYSIS])]
)
def test_temperature_diag(mock_diag_temperature, loop, expected, client):
    mock_diag_temperature.return_value = [1.0, 0.0, -1.0]

    response = client.get(f"/diag/temperature/{loop}/")

    assert response.status_code == 200
    assert response.json == [1.0, 0.0, -1.0]
    mock_diag_temperature.assert_called_once_with(*expected)


@mock.patch("unified_graphics.diag.temperature", autospec=True)
def test_temperature_diag_not_found(mock_diag_temperature, client):
    mock_diag_temperature.side_effect = FileNotFoundError()

    response = client.get("/diag/temperature/ges/")

    assert response.status_code == 404
    assert response.json == {"msg": "Diagnostic file not found"}


@mock.patch("unified_graphics.diag.temperature", autospec=True)
def test_temperature_diag_read_error(mock_diag_temperature, client):
    mock_diag_temperature.side_effect = ValueError()

    response = client.get("/diag/temperature/ges/")

    assert response.status_code == 500
    assert response.json == {"msg": "Unable to read diagnostic file"}


@mock.patch("unified_graphics.diag.wind", autospec=True)
def test_wind_diag(mock_diag_wind, client):
    mock_diag_wind.return_value = [
        VectorObservation(
            "WV270",
            "wind",
            PolarCoordinate(1, 180),
            PolarCoordinate(0.5, 0),
            PolarCoordinate(1, 90),
            Coordinate(0, 0),
        )
    ]
    response = client.get("/diag/wind/")

    mock_diag_wind.assert_called_once()

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "stationId": "WV270",
                    "variable": "wind",
                    "guess": {"magnitude": 1, "direction": 180},
                    "analysis": {"magnitude": 0.5, "direction": 0},
                    "observed": {"magnitude": 1, "direction": 90},
                },
                "geometry": {"type": "Point", "coordinates": [0, 0]},
            }
        ],
    }


@mock.patch("unified_graphics.diag.wind", autospec=True)
def test_wind_diag_read_error(mock_diag_wind, client):
    mock_diag_wind.side_effect = ValueError()

    response = client.get("/diag/wind/")

    assert response.status_code == 500
    assert response.json == {"msg": "Unable to read diagnostic file"}


def test_unknown_variable(client):
    response = client.get("/diag/not_a_variable/ges/")

    assert response.status_code == 404
    assert response.json == {"msg": "Variable not found: 'not_a_variable'"}
