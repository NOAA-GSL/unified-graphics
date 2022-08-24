from pathlib import Path
from unittest import mock

import pytest  # noqa: F401
import xarray as xr

from unified_graphics.diag import (
    Coordinate,
    PolarCoordinate,
    VectorObservation,
)


def test_root_endpoint(client):
    response = client.get("/")

    assert response.json == {"msg": "Hello, Dave"}


@pytest.mark.parametrize(
    "variable_name,variable_code",
    [("temperature", "t"), ("moisture", "q"), ("pressure", "p")],
)
def test_scalar_diag(variable_name, variable_code, diag_file, client):
    diag_file(
        f"ncdiag_conv_{variable_code}_ges.nc4.2022050514",
        xr.Dataset(
            {
                "Station_ID": xr.DataArray([b"WV270   ", b"E4294   "]),
                "Observation": xr.DataArray([0, 0]),
                "Obs_Minus_Forecast_adjusted": xr.DataArray([0, 0]),
                "Longitude": xr.DataArray([240, 272]),
                "Latitude": xr.DataArray([40, 30]),
            }
        ),
    )
    diag_file(
        f"ncdiag_conv_{variable_code}_anl.nc4.2022050514",
        xr.Dataset(
            {
                "Station_ID": xr.DataArray([b"WV270   ", b"E4294   "]),
                "Observation": xr.DataArray([0, 0]),
                "Obs_Minus_Forecast_adjusted": xr.DataArray([10, 10]),
                "Longitude": xr.DataArray([240, 272]),
                "Latitude": xr.DataArray([40, 30]),
            }
        ),
    )

    response = client.get(f"/diag/{variable_name}/")

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "stationId": "WV270",
                    "variable": variable_name,
                    "guess": 0,
                    "analysis": 10,
                    "observed": 0,
                },
                "geometry": {"type": "Point", "coordinates": [-120, 40]},
            },
            {
                "type": "Feature",
                "properties": {
                    "stationId": "E4294",
                    "variable": variable_name,
                    "guess": 0,
                    "analysis": 10,
                    "observed": 0,
                },
                "geometry": {"type": "Point", "coordinates": [-88, 30]},
            },
        ],
    }


@pytest.mark.parametrize("variable_name", ["temperature", "moisture", "pressure"])
def test_scalar_diag_not_found(variable_name, client):
    response = client.get(f"/diag/{variable_name}/")

    assert response.status_code == 404
    assert response.json == {"msg": "Diagnostic file not found"}


@pytest.mark.parametrize(
    "variable_name,variable_code",
    [("temperature", "t"), ("moisture", "q"), ("pressure", "p")],
)
def test_scalar_diag_read_error(variable_name, variable_code, app, client):
    empty = (
        Path(app.config["DIAG_DIR"]) / f"ncdiag_conv_{variable_code}_ges.nc4.2022050514"
    )
    empty.touch()

    response = client.get(f"/diag/{variable_name}/")

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
    response = client.get("/diag/not_a_variable/")

    assert response.status_code == 404
    assert response.json == {"msg": "Variable not found: 'not_a_variable'"}
