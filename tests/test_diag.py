import os
import uuid
from unittest import mock

import numpy as np
import pytest
import xarray as xr
from werkzeug.datastructures import MultiDict

from unified_graphics import diag
from unified_graphics.models import Analysis, WeatherModel

# Global resources for s3
test_bucket_name = "osti-modeling-dev-rtma-vis"


@pytest.fixture
def test_key_prefix():
    return f"/test/{uuid.uuid4()}/"


def test_get_model_metadata(session):
    model_run_list = [
        ("RTMA", "WCOSS", "CONUS", "REALTIME", "HRRR", "2023-03-17T14:00"),
        ("3DRTMA", "JET", "CONUS", "RETRO", "RRFS", "2023-03-17T15:00"),
    ]

    variable_list = ["ps", "q", "t", "uv"]

    for model, system, domain, freq, bg, init_time in model_run_list:
        wx_model = WeatherModel(name=model, background=WeatherModel(name=bg))
        analysis = Analysis(
            time=init_time,
            domain=domain,
            frequency=freq,
            system=system,
            model=wx_model,
        )
        session.add(analysis)

    result = diag.get_model_metadata(session)

    assert result
    assert result.model_list == ["3DRTMA", "RTMA"]
    assert result.system_list == ["JET", "WCOSS"]
    assert result.domain_list == ["CONUS"]
    assert result.frequency_list == ["REALTIME", "RETRO"]
    assert result.background_list == ["HRRR", "RRFS"]
    assert result.init_time_list == ["2023-03-17T14:00", "2023-03-17T15:00"]
    assert result.variable_list == variable_list


@pytest.mark.parametrize(
    "uri,expected",
    [
        ("file:///tmp/diag.zarr", "/tmp/diag.zarr"),
        ("/tmp/diag.zarr", "/tmp/diag.zarr"),
    ],
)
def test_get_store_file(uri, expected):
    result = diag.get_store(uri)

    assert result == expected


@mock.patch("unified_graphics.diag.S3Map", autospec=True)
@mock.patch("unified_graphics.diag.S3FileSystem", autospec=True)
def test_get_store_s3(mock_s3filesystem, mock_s3map):
    prev_env = dict(**os.environ)
    key = "test-key"
    token = "test-token"
    secret = "test-secret"
    client = {"region_name": "us-east-1"}
    uri = "s3://bucket/prefix/diag.zarr"

    os.environ["AWS_ACCESS_KEY_ID"] = key
    os.environ["AWS_SECRET_ACCESS_KEY"] = secret
    os.environ["AWS_SESSION_TOKEN"] = token

    result = diag.get_store(uri)

    assert result == mock_s3map.return_value
    mock_s3filesystem.assert_called_once_with(
        key=key, secret=secret, token=token, client_kwargs=client
    )
    mock_s3map.assert_called_once_with(
        root="bucket/prefix/diag.zarr", s3=mock_s3filesystem.return_value, check=False
    )

    os.environ = prev_env


def test_open_diagnostic(diag_zarr_file, diag_dataset, diag_zarr):
    variable = diag.Variable.PRESSURE
    init_time = "2022-05-13T06:00"
    loop = diag.MinimLoop.ANALYSIS
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    background = "HRRR"
    frequency = "REALTIME"

    diag_zarr(
        [variable.value],
        init_time,
        loop.value,
        model,
        system,
        domain,
        frequency,
        background,
    )

    result = diag.open_diagnostic(
        diag_zarr_file,
        model,
        system,
        domain,
        background,
        frequency,
        variable,
        init_time,
        loop,
    )

    xr.testing.assert_equal(
        result,
        diag_dataset(
            str(variable), init_time, str(loop), model, system, frequency, background
        ),
    )


def test_open_diagnostic_local_does_not_exist(diag_zarr_file):
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    background = "HRRR"
    frequency = "REALTIME"
    init_time = "2022-05-16T04:00"
    expected = r"No such file or directory: '.*test_diag.zarr'$"

    with pytest.raises(FileNotFoundError, match=expected):
        diag.open_diagnostic(
            diag_zarr_file,
            model,
            system,
            domain,
            background,
            frequency,
            diag.Variable.WIND,
            init_time,
            diag.MinimLoop.GUESS,
        )


@pytest.mark.parametrize(
    "uri,expected",
    [
        (
            "foo://an/unknown/uri.zarr",
            "Unsupported protocol 'foo' for URI: 'foo://an/unknown/uri.zarr'",
        ),
        (
            "ftp://an/unsupported/uri.zarr",
            "Unsupported protocol 'ftp' for URI: 'ftp://an/unsupported/uri.zarr'",
        ),
    ],
)
def test_open_diagnostic_unknown_uri(uri, expected):
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    background = "HRRR"
    frequency = "REALTIME"
    init_time = "2022-05-16T04:00"

    with pytest.raises(ValueError, match=expected):
        diag.open_diagnostic(
            uri,
            model,
            system,
            domain,
            background,
            frequency,
            diag.Variable.WIND,
            init_time,
            diag.MinimLoop.GUESS,
        )


@pytest.mark.aws
def test_open_diagnostic_s3_nonexistent_bucket():
    init_time = "2022-05-05T14:00"
    diag_zarr_file = "s3://foo/test.zarr"

    expected = r"Forbidden"

    with pytest.raises(PermissionError, match=expected):
        diag.open_diagnostic(
            diag_zarr_file, diag.Variable.WIND, init_time, diag.MinimLoop.GUESS
        )


@pytest.mark.aws
def test_open_diagnostic_s3_nonexistent_key():
    init_time = "2022-05-16T04:00"
    diag_zarr_file = "s3://osti-modeling-dev-rtma-vis/test/no_such.zarr"
    expected = r"No such file or directory.*"

    with pytest.raises(FileNotFoundError, match=expected):
        diag.open_diagnostic(
            diag_zarr_file, diag.Variable.WIND, init_time, diag.MinimLoop.GUESS
        )


@pytest.mark.aws
def test_open_diagnostic_s3_unauthenticated(test_key_prefix):
    # Back up the current environment so we don't break anything
    prev_env = dict(**os.environ)

    init_time = "2022-05-16T04:00"
    diag_zarr_file = f"s3://{test_bucket_name}{test_key_prefix}diag.zarr"

    del os.environ["AWS_ACCESS_KEY_ID"]
    del os.environ["AWS_SECRET_ACCESS_KEY"]
    del os.environ["AWS_SESSION_TOKEN"]

    with pytest.raises(PermissionError):
        diag.open_diagnostic(
            diag_zarr_file, diag.Variable.WIND, init_time, diag.MinimLoop.GUESS
        )

    # Restore environment
    os.environ = prev_env


@pytest.mark.aws
def test_open_diagnostic_s3(test_key_prefix, diag_zarr, diag_dataset):
    variable = diag.Variable.WIND
    loop = diag.MinimLoop.ANALYSIS
    coords = {"component": ["u", "v"]}
    init_time = "2022-05-05T14:00"
    zarr_file = f"s3://{test_bucket_name}{test_key_prefix}diag.zarr"
    diag_zarr([variable.value], init_time, loop.value, zarr_file)

    result = diag.open_diagnostic(zarr_file, variable, init_time, loop)

    xr.testing.assert_equal(
        result, diag_dataset(variable.value, init_time, loop.value, **coords)
    )


# Test cases taken from the examples at
# http://ncl.ucar.edu/Document/Functions/Contributed/wind_direction.shtml
@pytest.mark.parametrize(
    "u,v,expected",
    (
        [
            np.array([10, 0, 0, -10, 10, 10, -10, -10]),
            np.array([0, 10, -10, 0, 10, -10, 10, -10]),
            np.array([270, 180, 0, 90, 225, 315, 135, 45]),
        ],
        [
            np.array([0.0, -0.0, 0.0, -0.0]),
            np.array([0.0, 0.0, -0.0, -0.0]),
            np.array([0.0, 0.0, 0.0, 0.0]),
        ],
    ),
)
def test_vector_direction(u, v, expected):
    result = diag.vector_direction(u, v)

    np.testing.assert_array_almost_equal(result, expected, decimal=5)


def test_vector_magnitude():
    u = np.array([1, 0, 1, 0])
    v = np.array([0, 1, 1, 0])

    result = diag.vector_magnitude(u, v)

    np.testing.assert_array_almost_equal(
        result, np.array([1, 1, 1.41421, 0]), decimal=5
    )


@pytest.mark.parametrize(
    "mapping,expected",
    [
        ([("a", "1")], [("a", np.array([1.0]), np.array([1.0]))]),
        ([("a", "1::2")], [("a", np.array([1.0]), np.array([2.0]))]),
        ([("a", "2,4::3,1")], [("a", np.array([2.0, 1.0]), np.array([3.0, 4.0]))]),
    ],
)
def test_get_bounds(mapping, expected):
    filters = MultiDict(mapping)

    result = list(diag.get_bounds(filters))

    for (coord, lower, upper), (expected_coord, expected_lower, expected_upper) in zip(
        result, expected
    ):
        assert coord == expected_coord
        assert (lower == expected_lower).all()
        assert (upper == expected_upper).all()
