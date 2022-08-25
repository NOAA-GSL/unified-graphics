from pathlib import Path

import pytest  # noqa: F401
import xarray as xr


def test_root_endpoint(client):
    response = client.get("/")

    assert response.json == {"diagnostics": "/diag/"}


def test_list_variables(client):
    response = client.get("/diag/")

    assert response.status_code == 200
    assert response.json == {
        "moisture": "/diag/moisture/",
        "pressure": "/diag/pressure/",
        "temperature": "/diag/temperature/",
        "wind": "/diag/wind/",
    }


@pytest.mark.parametrize(
    "variable_name,variable_code",
    [("temperature", "t"), ("moisture", "q"), ("pressure", "ps")],
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
                    "type": "scalar",
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
                    "type": "scalar",
                    "variable": variable_name,
                    "guess": 0,
                    "analysis": 10,
                    "observed": 0,
                },
                "geometry": {"type": "Point", "coordinates": [-88, 30]},
            },
        ],
    }


def test_wind_diag(diag_file, client):
    diag_file(
        "ncdiag_conv_uv_ges.nc4.2022050514",
        xr.Dataset(
            {
                "Station_ID": xr.DataArray([b"WV270   ", b"E4294   "]),
                "u_Observation": xr.DataArray([1, 0]),
                "v_Observation": xr.DataArray([0, 1]),
                "u_Obs_Minus_Forecast_adjusted": xr.DataArray([0.5, 0]),
                "v_Obs_Minus_Forecast_adjusted": xr.DataArray([0, 0.5]),
                "Longitude": xr.DataArray([240, 272]),
                "Latitude": xr.DataArray([40, 30]),
            }
        ),
    )
    diag_file(
        "ncdiag_conv_uv_anl.nc4.2022050514",
        xr.Dataset(
            {
                "Station_ID": xr.DataArray([b"WV270   ", b"E4294   "]),
                "u_Observation": xr.DataArray([1, 0]),
                "v_Observation": xr.DataArray([0, 1]),
                "u_Obs_Minus_Forecast_adjusted": xr.DataArray([0.1, 0]),
                "v_Obs_Minus_Forecast_adjusted": xr.DataArray([0, 0.1]),
                "Longitude": xr.DataArray([240, 272]),
                "Latitude": xr.DataArray([40, 30]),
            }
        ),
    )

    response = client.get("/diag/wind/")

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "stationId": "WV270",
                    "type": "vector",
                    "variable": "wind",
                    "guess": {"magnitude": 0.5, "direction": 270.0},
                    "analysis": {"magnitude": 0.1, "direction": 270.0},
                    "observed": {"magnitude": 1.0, "direction": 270.0},
                },
                "geometry": {"type": "Point", "coordinates": [-120.0, 40.0]},
            },
            {
                "type": "Feature",
                "properties": {
                    "stationId": "E4294",
                    "type": "vector",
                    "variable": "wind",
                    "guess": {"magnitude": 0.5, "direction": 180.0},
                    "analysis": {"magnitude": 0.1, "direction": 180.0},
                    "observed": {"magnitude": 1.0, "direction": 180.0},
                },
                "geometry": {"type": "Point", "coordinates": [-88.0, 30.0]},
            },
        ],
    }


@pytest.mark.parametrize(
    "variable_name", ["temperature", "moisture", "pressure", "wind"]
)
def test_diag_not_found(variable_name, client):
    response = client.get(f"/diag/{variable_name}/")

    assert response.status_code == 404
    assert response.json == {"msg": "Diagnostic file not found"}


@pytest.mark.parametrize(
    "variable_name,variable_code",
    [("temperature", "t"), ("moisture", "q"), ("pressure", "ps"), ("wind", "uv")],
)
def test_diag_read_error(variable_name, variable_code, app, client):
    empty = (
        Path(app.config["DIAG_DIR"]) / f"ncdiag_conv_{variable_code}_ges.nc4.2022050514"
    )
    empty.touch()

    response = client.get(f"/diag/{variable_name}/")

    assert response.status_code == 500
    assert response.json == {"msg": "Unable to read diagnostic file"}


def test_unknown_variable(client):
    response = client.get("/diag/not_a_variable/")

    assert response.status_code == 404
    assert response.json == {"msg": "Variable not found: 'not_a_variable'"}
