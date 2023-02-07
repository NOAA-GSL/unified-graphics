from pathlib import Path

import pytest  # noqa: F401


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
def test_scalar_diag(variable_name, variable_code, diag_zarr, client):
    init_time = "2022-05-16T04:00"
    diag_zarr([variable_code], init_time, "ges")
    diag_zarr([variable_code], init_time, "anl")

    response = client.get(f"/diag/{variable_name}/{init_time}")

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "type": "scalar",
                    "variable": variable_name,
                    "guess": 0,
                    "analysis": 0,
                    "observed": 0,
                },
                "geometry": {"type": "Point", "coordinates": [90, 22]},
            },
            {
                "type": "Feature",
                "properties": {
                    "type": "scalar",
                    "variable": variable_name,
                    "guess": 0,
                    "analysis": 0,
                    "observed": 0,
                },
                "geometry": {"type": "Point", "coordinates": [-160, 25]},
            },
        ],
    }


def test_wind_diag(diag_zarr, client):
    init_time = "2022-05-16T04:00"
    diag_zarr(["uv"], init_time, "ges")
    diag_zarr(["uv"], init_time, "anl")

    response = client.get(f"/diag/wind/{init_time}")

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "type": "vector",
                    "variable": "wind",
                    "guess": {"magnitude": 0.0, "direction": 0.0},
                    "analysis": {"magnitude": 0.0, "direction": 0.0},
                    "observed": {"magnitude": 0.0, "direction": 0.0},
                },
                "geometry": {"type": "Point", "coordinates": [90, 22]},
            },
            {
                "type": "Feature",
                "properties": {
                    "type": "vector",
                    "variable": "wind",
                    "guess": {"magnitude": 0.0, "direction": 0.0},
                    "analysis": {"magnitude": 0.0, "direction": 0.0},
                    "observed": {"magnitude": 0.0, "direction": 0.0},
                },
                "geometry": {"type": "Point", "coordinates": [-160.0, 25.0]},
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
        Path(app.config["DIAG_DIR"].removeprefix("file://"))
        / f"ncdiag_conv_{variable_code}_ges.nc4.2022050514"
    )
    empty.touch()

    response = client.get(f"/diag/{variable_name}/")

    assert response.status_code == 500
    assert response.json == {"msg": "Unable to read diagnostic file"}


def test_unknown_variable(client):
    response = client.get("/diag/not_a_variable/")

    assert response.status_code == 404
    assert response.json == {"msg": "Variable not found: 'not_a_variable'"}
