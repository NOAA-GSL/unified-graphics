from pathlib import Path

import pytest  # noqa: F401
import xarray as xr


@pytest.mark.xfail(reason="Needs to be updated to expect HTML response")
def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200


@pytest.mark.parametrize(
    "variable_name,variable_code,loop",
    [("temperature", "t", "anl"), ("moisture", "q", "ges")],
)
def test_scalar_diag(variable_name, variable_code, loop, diag_zarr, client):
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    background = "HRRR"
    frequency = "REALTIME"
    init_time = "2022-05-16T04:00"
    diag_zarr([variable_code], init_time, loop)

    response = client.get(
        f"/diag/{model}/{system}/{domain}/{background}/{frequency}"
        f"/{variable_code}/{init_time}/{loop}/"
    )

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "type": "scalar",
                    "loop": loop,
                    "variable": variable_name,
                    "adjusted": 0,
                    "unadjusted": 0,
                    "observed": 0,
                },
                "geometry": {"type": "Point", "coordinates": [90, 22]},
            },
            {
                "type": "Feature",
                "properties": {
                    "type": "scalar",
                    "loop": loop,
                    "variable": variable_name,
                    "adjusted": 0,
                    "unadjusted": 0,
                    "observed": 0,
                },
                "geometry": {"type": "Point", "coordinates": [-160, 25]},
            },
        ],
    }


def test_wind_diag(diag_zarr, client):
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    background = "HRRR"
    frequency = "REALTIME"
    init_time = "2022-05-16T04:00"
    loop = "ges"
    diag_zarr(["uv"], init_time, loop)

    response = client.get(
        f"/diag/{model}/{system}/{domain}/{background}"
        f"/{frequency}/uv/{init_time}/{loop}/"
    )

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "type": "vector",
                    "variable": "wind",
                    "loop": loop,
                    "adjusted": {"u": 0.0, "v": 0.0},
                    "unadjusted": {"u": 0.0, "v": 0.0},
                    "observed": {"u": 0.0, "v": 0.0},
                },
                "geometry": {"type": "Point", "coordinates": [90, 22]},
            },
            {
                "type": "Feature",
                "properties": {
                    "type": "vector",
                    "variable": "wind",
                    "loop": loop,
                    "adjusted": {"u": 0.0, "v": 0.0},
                    "unadjusted": {"u": 0.0, "v": 0.0},
                    "observed": {"u": 0.0, "v": 0.0},
                },
                "geometry": {"type": "Point", "coordinates": [-160.0, 25.0]},
            },
        ],
    }


def test_vector_magnitude(diag_zarr, client):
    init_time = "2022-05-16T04:00"
    loop = "ges"
    diag_zarr(["uv"], init_time, loop)

    response = client.get(f"/diag/wind/{init_time}/{loop}/magnitude/")

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "type": "vector",
                    "variable": "wind",
                    "loop": loop,
                    "adjusted": 0.0,
                    "unadjusted": 0.0,
                    "observed": 0.0,
                },
                "geometry": {"type": "Point", "coordinates": [90, 22]},
            },
            {
                "type": "Feature",
                "properties": {
                    "type": "vector",
                    "variable": "wind",
                    "loop": loop,
                    "adjusted": 0.0,
                    "unadjusted": 0.0,
                    "observed": 0.0,
                },
                "geometry": {"type": "Point", "coordinates": [-160.0, 25.0]},
            },
        ],
    }


def test_region_filter_scalar(diag_zarr, client):
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    background = "HRRR"
    frequency = "REALTIME"
    init_time = "2022-05-16T04:00"
    loop = "ges"
    variable = "t"
    variable_name = "temperature"
    diag_zarr([variable], init_time, loop)

    url = (
        f"/diag/{model}/{system}/{domain}/{background}"
        f"/{frequency}/{variable}/{init_time}/{loop}/"
    )
    query = "longitude=-160.1::-159.9&latitude=27::22"
    response = client.get(f"{url}?{query}")

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "type": "scalar",
                    "loop": loop,
                    "variable": variable_name,
                    "adjusted": 0,
                    "unadjusted": 0,
                    "observed": 0,
                },
                "geometry": {"type": "Point", "coordinates": [-160, 25]},
            },
        ],
    }


def test_range_filter_scalar(diag_zarr, client):
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    frequency = "REALTIME"
    background = "HRRR"
    init_time = "2022-05-16T04:00"
    loop = "ges"
    variable = "t"
    variable_name = "temperature"
    data = xr.Dataset(
        {
            "obs_minus_forecast_adjusted": (["nobs"], [0, 1]),
            "obs_minus_forecast_unadjusted": (["nobs"], [0, 2]),
            "observation": (["nobs"], [0, 2]),
            "forecast_adjusted": (["nobs"], [0, 1]),
            "forecast_unadjusted": (["nobs"], [0, 0]),
        },
        coords=dict(
            longitude=(["nobs"], [90, -160]),
            latitude=(["nobs"], [22, 25]),
            is_used=(["nobs"], [0, 1]),
        ),
        attrs={
            "name": variable,
            "loop": loop,
            "initialization_time": init_time,
            "model": model,
            "system": system,
            "domain": domain,
            "frequency": frequency,
            "background": background,
        },
    )
    diag_zarr([variable], init_time, loop, model, system, domain, frequency, data=data)

    url = (
        f"/diag/{model}/{system}/{domain}/{background}"
        f"/{frequency}/{variable}/{init_time}/{loop}/"
    )
    query = "obs_minus_forecast_adjusted=1.5::1"
    response = client.get(f"{url}?{query}")

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "type": "scalar",
                    "loop": loop,
                    "variable": variable_name,
                    "adjusted": 1,
                    "unadjusted": 2,
                    "observed": 2,
                },
                "geometry": {"type": "Point", "coordinates": [-160, 25]},
            },
        ],
    }


def test_region_filter_vector(diag_zarr, client):
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    background = "HRRR"
    frequency = "REALTIME"
    init_time = "2022-05-16T04:00"
    loop = "ges"
    variable = "uv"
    variable_name = "wind"
    diag_zarr([variable], init_time, loop)

    url = (
        f"/diag/{model}/{system}/{domain}/{background}"
        f"/{frequency}/{variable}/{init_time}/{loop}/"
    )
    query = "longitude=-160.1::-159.9&latitude=27::22"
    response = client.get(f"{url}?{query}")

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "type": "vector",
                    "variable": variable_name,
                    "loop": loop,
                    "adjusted": {"u": 0.0, "v": 0.0},
                    "unadjusted": {"u": 0.0, "v": 0.0},
                    "observed": {"u": 0.0, "v": 0.0},
                },
                "geometry": {"type": "Point", "coordinates": [-160.0, 25.0]},
            },
        ],
    }


def test_range_filter_vector(diag_zarr, client):
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    frequency = "REALTIME"
    background = "HRRR"
    init_time = "2022-05-16T04:00"
    loop = "ges"
    variable = "uv"
    variable_name = "wind"
    data = xr.Dataset(
        {
            "obs_minus_forecast_adjusted": (["nobs", "component"], [[0, 1], [10, 20]]),
            "obs_minus_forecast_unadjusted": (
                ["nobs", "component"],
                [[0, 2], [10, 25]],
            ),
            "observation": (["nobs", "component"], [[0, 2], [20, 50]]),
            "forecast_adjusted": (["nobs", "component"], [[0, 1], [10, 30]]),
            "forecast_unadjusted": (["nobs", "component"], [[0, 0], [10, 25]]),
        },
        coords=dict(
            component=["u", "v"],
            longitude=(["nobs"], [90, -160]),
            latitude=(["nobs"], [22, 25]),
            is_used=(["nobs"], [1, 0]),
        ),
        attrs={
            "name": variable,
            "loop": loop,
            "initialization_time": init_time,
            "model": model,
            "system": system,
            "domain": domain,
            "frequency": frequency,
            "background": background,
        },
    )
    diag_zarr([variable], init_time, loop, data=data)

    url = (
        f"/diag/{model}/{system}/{domain}/{background}"
        f"/{frequency}/{variable}/{init_time}/{loop}/"
    )
    # This query is designed so that both observations v components fall within the
    # selected region, but only the first observation's u component does, so only the
    # first observation should be returned
    query = "obs_minus_forecast_adjusted=1::-1&obs_minus_forecast_adjusted=0::25"
    response = client.get(f"{url}?{query}")

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "type": "vector",
                    "variable": variable_name,
                    "loop": loop,
                    "adjusted": {"u": 0, "v": 1},
                    "unadjusted": {"u": 0, "v": 2},
                    "observed": {"u": 0, "v": 2},
                },
                "geometry": {"type": "Point", "coordinates": [90, 22]},
            },
        ],
    }


def test_unused_filter(diag_zarr, client):
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    background = "HRRR"
    frequency = "REALTIME"
    variable_code = "t"
    variable_name = "temperature"
    loop = "ges"
    init_time = "2022-05-16T04:00"
    diag_zarr([variable_code], init_time, loop)

    url = (
        f"/diag/{model}/{system}/{domain}/{background}"
        f"/{frequency}/{variable_code}/{init_time}/{loop}/"
    )
    query = "is_used=false"
    response = client.get(f"{url}?{query}")

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "type": "scalar",
                    "loop": loop,
                    "variable": variable_name,
                    "adjusted": 0,
                    "unadjusted": 0,
                    "observed": 0,
                },
                "geometry": {"type": "Point", "coordinates": [91, 23]},
            },
        ],
    }


def test_all_obs_filter(diag_zarr, client):
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    background = "HRRR"
    frequency = "REALTIME"
    variable_code = "t"
    variable_name = "temperature"
    loop = "ges"
    init_time = "2022-05-16T04:00"
    diag_zarr([variable_code], init_time, loop)

    url = (
        f"/diag/{model}/{system}/{domain}/{background}"
        f"/{frequency}/{variable_code}/{init_time}/{loop}/"
    )
    query = "is_used=true::false"
    response = client.get(f"{url}?{query}")

    assert response.status_code == 200
    assert response.json == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "type": "scalar",
                    "loop": loop,
                    "variable": variable_name,
                    "adjusted": 0,
                    "unadjusted": 0,
                    "observed": 0,
                },
                "geometry": {"type": "Point", "coordinates": [90, 22]},
            },
            {
                "type": "Feature",
                "properties": {
                    "type": "scalar",
                    "loop": loop,
                    "variable": variable_name,
                    "adjusted": 0,
                    "unadjusted": 0,
                    "observed": 0,
                },
                "geometry": {"type": "Point", "coordinates": [91, 23]},
            },
            {
                "type": "Feature",
                "properties": {
                    "type": "scalar",
                    "loop": loop,
                    "variable": variable_name,
                    "adjusted": 0,
                    "unadjusted": 0,
                    "observed": 0,
                },
                "geometry": {"type": "Point", "coordinates": [-160, 25]},
            },
        ],
    }


@pytest.mark.parametrize("variable", ["t", "q", "ps", "uv"])
def test_diag_not_found(variable, client):
    response = client.get(
        f"/diag/RTMA/WCOSS/CONUS/HRRR/REALTIME/{variable}/2022-05-05T14:00/ges/"
    )

    assert response.status_code == 404
    assert response.json == {"msg": "Diagnostic file not found"}


@pytest.mark.parametrize(
    "variable",
    ["t", "q", "ps", "uv"],
)
def test_diag_read_error(variable, app, client):
    Path(app.config["DIAG_ZARR"]).touch()

    response = client.get(
        f"/diag/RTMA/WCOSS/CONUS/HRRR/REALTIME/{variable}/2022-05-05T14:00/ges/"
    )

    assert response.status_code == 500
    assert response.json == {"msg": "Unable to read diagnostic file"}


@pytest.mark.parametrize(
    "url",
    [
        "not_a_variable/2022-05-05T14:00/ges/",
    ],
)
def test_unknown_variable(url, client):
    response = client.get(f"/diag/RTMA/WCOSS/CONUS/HRRR/REALTIME/{url}")

    assert response.status_code == 404
    assert response.json == {"msg": "Variable not found: 'not_a_variable'"}
