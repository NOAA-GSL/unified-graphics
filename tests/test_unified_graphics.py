from pathlib import Path

import pytest  # noqa: F401
import xarray as xr

from unified_graphics import create_app


def get_group(ds: xr.Dataset) -> str:
    return "/".join(
        [
            ds.model,
            ds.system,
            ds.domain,
            ds.background,
            ds.frequency,
            ds.name,
            ds.initialization_time,
            ds.loop,
        ]
    )


def save(store: Path, data: xr.Dataset):
    data.to_zarr(store, group=get_group(data), consolidated=False)


@pytest.fixture(scope="module")
def model():
    return {
        "model": "3DRTMA",
        "system": "WCOSS",
        "domain": "CONUS",
        "background": "HRRR",
        "frequency": "REALTIME",
    }


@pytest.fixture
def diag_zarr_path(tmp_path):
    return tmp_path / "test_diag.zarr"


@pytest.fixture
def t(model, diag_zarr_path, test_dataset):
    ds = test_dataset(
        **model,
        initialization_time="2022-05-16T04:00",
        loop="ges",
        variable="t",
        observation=[1, 0, 2],
        forecast_unadjusted=[0, 1, -1],
        longitude=[90, 91, 89],
        latitude=[22, 23, 24],
        is_used=[1, 1, 0],
    )

    save(diag_zarr_path, ds)

    return ds


@pytest.fixture
def uv(model, diag_zarr_path, test_dataset):
    ds = test_dataset(
        **model,
        variable="uv",
        initialization_time="2022-05-16T04:00",
        loop="ges",
        observation=[[0, 1], [1, 0]],
        forecast_unadjusted=[[0, 0], [1, 1]],
        longitude=[90, 91],
        latitude=[22, 23],
        is_used=[1, 1],
        component=["u", "v"],
    )

    save(diag_zarr_path, ds)

    return ds


@pytest.fixture
def app(tmp_path, diag_zarr_path, test_db):
    _app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": test_db,
            "DIAG_ZARR": str(diag_zarr_path),
            "DIAG_PARQUET": f"file://{tmp_path}",
        }
    )

    _app.testing = True

    yield _app


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.mark.xfail(reason="Needs to be updated to expect HTML response")
def test_home_page(client):
    assert 0


def test_scalar_diag(t, client):
    # Arrange
    group = get_group(t)

    # Act
    response = client.get(f"/diag/{group}/")

    # Assert
    assert response.json == [
        {
            "obs_minus_forecast_adjusted": 1.0,
            "obs_minus_forecast_unadjusted": 1.0,
            "observation": 1.0,
            "longitude": 90.0,
            "latitude": 22.0,
        },
        {
            "obs_minus_forecast_adjusted": -1.0,
            "obs_minus_forecast_unadjusted": -1.0,
            "observation": 0.0,
            "longitude": 91.0,
            "latitude": 23.0,
        },
    ]


def test_scalar_history(model, diag_parquet, client, test_dataset):
    # Arrange
    run_list = [
        {
            "initialization_time": "2022-05-16T04:00",
            "observation": [10, 20],
            "forecast_unadjusted": [5, 10],
            "is_used": [True, True],
            # O - F [5, 10]
        },
        {
            "initialization_time": "2022-05-16T07:00",
            "observation": [1, 2, 3],
            "forecast_unadjusted": [5, 10, 3],
            "longitude": [0, 0, 0],
            "latitude": [0, 0, 0],
            "is_used": [True, True, True],
            # O - F [-4, -8, 0]
        },
    ]

    for run in run_list:
        data = test_dataset(
            **model,
            variable="ps",
            loop="ges",
            **run,
        )
        diag_parquet(data)

    # Act
    response = client.get("/diag/3DRTMA/WCOSS/CONUS/HRRR/REALTIME/ps/ges/")

    # Assert
    assert response.json == [
        {
            "initialization_time": "2022-05-16T04:00",
            "min": 5.0,
            "max": 10.0,
            "mean": 7.5,
            "count": 2,
        },
        {
            "initialization_time": "2022-05-16T07:00",
            "min": -8.0,
            "max": 0.0,
            "mean": -4.0,
            "count": 3,
        },
    ]


def test_scalar_history_unused(model, diag_parquet, client, test_dataset):
    # Arrange
    run_list = [
        {
            "initialization_time": "2022-05-16T04:00",
            "observation": [10, 20],
            "forecast_unadjusted": [5, 10],
            "is_used": [True, False],
            # O - F [5, 10]
        },
        {
            "initialization_time": "2022-05-16T07:00",
            "observation": [1, 2],
            "forecast_unadjusted": [5, 10],
            "is_used": [False, True],
            # O - F [-4, -8]
        },
    ]

    for run in run_list:
        data = test_dataset(
            **model,
            variable="ps",
            loop="ges",
            **run,
        )
        diag_parquet(data)

    # Act
    response = client.get("/diag/3DRTMA/WCOSS/CONUS/HRRR/REALTIME/ps/ges/")

    # Assert
    assert response.json == [
        {
            "initialization_time": "2022-05-16T04:00",
            "min": 5.0,
            "max": 5.0,
            "mean": 5.0,
            "count": 1,
        },
        {
            "initialization_time": "2022-05-16T07:00",
            "min": -8.0,
            "max": -8.0,
            "mean": -8.0,
            "count": 1,
        },
    ]


def test_scalar_history_empty(model, diag_parquet, test_dataset, client):
    # Arrange
    run_list = [
        {
            "initialization_time": "2022-05-16T04:00",
            "is_used": [False, False],
        },
        {
            "initialization_time": "2022-05-16T07:00",
            "is_used": [False, False],
        },
    ]

    for run in run_list:
        data = test_dataset(
            **model,
            variable="ps",
            loop="ges",
            **run,
        )
        diag_parquet(data)

    # Act
    response = client.get("/diag/3DRTMA/WCOSS/CONUS/HRRR/REALTIME/ps/ges/")

    # Assert
    assert response.json == []


@pytest.mark.xfail
def test_vector_history():
    assert 0, "Not implemented"


def test_wind_diag(uv, client):
    # Arrange
    group = get_group(uv)

    # Act
    response = client.get(f"/diag/{group}/")

    # Assert
    assert response.json == [
        {
            "obs_minus_forecast_adjusted_u": 0.0,
            "obs_minus_forecast_adjusted_v": 1.0,
            "obs_minus_forecast_unadjusted_u": 0.0,
            "obs_minus_forecast_unadjusted_v": 1.0,
            "observation_u": 0.0,
            "observation_v": 1.0,
            "longitude_u": 90.0,
            "longitude_v": 90.0,
            "latitude_u": 22.0,
            "latitude_v": 22.0,
        },
        {
            "obs_minus_forecast_adjusted_u": 0.0,
            "obs_minus_forecast_adjusted_v": -1.0,
            "obs_minus_forecast_unadjusted_u": 0.0,
            "obs_minus_forecast_unadjusted_v": -1.0,
            "observation_u": 1.0,
            "observation_v": 0.0,
            "longitude_u": 91.0,
            "longitude_v": 91.0,
            "latitude_u": 23.0,
            "latitude_v": 23.0,
        },
    ]


def test_vector_magnitude(uv, client):
    # Arrange
    group = get_group(uv)

    # Act
    response = client.get(f"/diag/{group}/magnitude/")

    # Assert
    assert response.json == [
        {
            "obs_minus_forecast_adjusted": 1.0,
            "obs_minus_forecast_unadjusted": 1.0,
            "observation": 1.0,
            "longitude": 90.0,
            "latitude": 22.0,
        },
        {
            "obs_minus_forecast_adjusted": 1.0,
            "obs_minus_forecast_unadjusted": 1.0,
            "observation": 1.0,
            "longitude": 91.0,
            "latitude": 23.0,
        },
    ]


def test_region_filter_scalar(t, client):
    group = get_group(t)

    url = f"/diag/{group}/"
    query = "longitude=89.9::90.5&latitude=27::22"
    response = client.get(f"{url}?{query}")

    assert response.json == [
        {
            "obs_minus_forecast_adjusted": 1.0,
            "obs_minus_forecast_unadjusted": 1.0,
            "observation": 1.0,
            "longitude": 90.0,
            "latitude": 22.0,
        },
    ]


def test_range_filter_scalar(t, client):
    # Arrange
    group = get_group(t)
    url = f"/diag/{group}/"
    query = "obs_minus_forecast_adjusted=1.5::1"

    # Act
    response = client.get(f"{url}?{query}")

    # Assert
    assert response.json == [
        {
            "obs_minus_forecast_adjusted": 1.0,
            "obs_minus_forecast_unadjusted": 1.0,
            "observation": 1.0,
            "longitude": 90.0,
            "latitude": 22.0,
        },
    ]


def test_region_filter_vector(uv, client):
    # Arrange
    group = get_group(uv)
    url = f"/diag/{group}/"
    query = "longitude=89.9::90.5&latitude=27::22"

    # Act
    response = client.get(f"{url}?{query}")

    assert response.json == [
        {
            "obs_minus_forecast_adjusted_u": 0.0,
            "obs_minus_forecast_adjusted_v": 1.0,
            "obs_minus_forecast_unadjusted_u": 0.0,
            "obs_minus_forecast_unadjusted_v": 1.0,
            "observation_u": 0.0,
            "observation_v": 1.0,
            "longitude_u": 90.0,
            "longitude_v": 90.0,
            "latitude_u": 22.0,
            "latitude_v": 22.0,
        },
    ]


# BUG: This test is missing a test case
#
# I'm not sure why, but this test was passing when it probably should have failed. It
# looked to me like in production when we applied a range filter, we would end up with
# data that looked like this:
#
# [
#     [1, 1],
#     [1, NaN],
# ]
#
# That second row should be filtered out. I thought this test was testing this case, but
# the test was passing while in production we were getting JSON parse errors because of
# the Nan values. You can see the fix in commit 7f92e15fbdcde7fd683143f6bf429f2b45fac3d2
# that got this working in production, but I was unable to reproduce the issue in
# the test.
def test_range_filter_vector(uv, client):
    # Arrange
    group = get_group(uv)
    url = f"/diag/{group}/"

    # This query is designed so that both observations v components fall within the
    # selected region, but only the first observation's u component does, so only the
    # first observation should be returned
    query = "obs_minus_forecast_adjusted=1::-0.5&obs_minus_forecast_adjusted=0::25"

    # Act
    response = client.get(f"{url}?{query}")

    # Assert
    assert response.json == [
        {
            "obs_minus_forecast_adjusted_u": 0.0,
            "obs_minus_forecast_adjusted_v": 1.0,
            "obs_minus_forecast_unadjusted_u": 0.0,
            "obs_minus_forecast_unadjusted_v": 1.0,
            "observation_u": 0.0,
            "observation_v": 1.0,
            "longitude_u": 90.0,
            "longitude_v": 90.0,
            "latitude_u": 22.0,
            "latitude_v": 22.0,
        },
    ]


def test_unused_filter(t, client):
    # Arrange
    group = get_group(t)
    url = f"/diag/{group}/"
    query = "is_used=false"

    # Act
    response = client.get(f"{url}?{query}")

    # Assert
    assert response.json == [
        {
            "obs_minus_forecast_adjusted": 3.0,
            "obs_minus_forecast_unadjusted": 3.0,
            "observation": 2.0,
            "longitude": 89.0,
            "latitude": 24.0,
        },
    ]


def test_all_obs_filter(t, client):
    group = get_group(t)

    url = f"/diag/{group}/"
    query = "is_used=true::false"
    response = client.get(f"{url}?{query}")

    assert response.status_code == 200
    assert response.json == [
        {
            "obs_minus_forecast_adjusted": 1.0,
            "obs_minus_forecast_unadjusted": 1.0,
            "observation": 1.0,
            "longitude": 90.0,
            "latitude": 22.0,
        },
        {
            "obs_minus_forecast_adjusted": -1.0,
            "obs_minus_forecast_unadjusted": -1.0,
            "observation": 0.0,
            "longitude": 91.0,
            "latitude": 23.0,
        },
        {
            "obs_minus_forecast_adjusted": 3.0,
            "obs_minus_forecast_unadjusted": 3.0,
            "observation": 2.0,
            "longitude": 89.0,
            "latitude": 24.0,
        },
    ]


@pytest.mark.parametrize("variable", ["t", "q", "ps", "uv"])
def test_diag_not_found(variable, client):
    response = client.get(
        f"/diag/RTMA/WCOSS/CONUS/HRRR/REALTIME/{variable}/2022-05-05T14:00/ges/"
    )

    assert response.status_code == 404
    assert response.json == {"msg": "Diagnostic file group not found"}


@pytest.mark.parametrize(
    "variable",
    ["t", "q", "ps", "uv"],
)
def test_diag_read_error(variable, app, client):
    Path(app.config["DIAG_ZARR"].replace("file://", "")).touch()

    response = client.get(
        f"/diag/RTMA/WCOSS/CONUS/HRRR/REALTIME/{variable}/2022-05-05T14:00/ges/"
    )

    assert response.status_code == 500
    assert response.json == {"msg": "Unable to read diagnostic file group"}


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
