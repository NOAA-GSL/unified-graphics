import os
import time
import uuid
from pathlib import Path

import numpy as np
import pytest
import requests
import xarray as xr

from unified_graphics import create_app, diag

# Global resources for s3
test_bucket_name = "osti-modeling-dev-rtma-vis"
port = 5555
endpoint_uri = f"http://127.0.0.1:{port}/"


@pytest.fixture
def test_key_prefix():
    return f"/test/{uuid.uuid4()}/"


# Fixture taken from fsspec/s3fs's test suite at
# https://github.com/fsspec/s3fs/blob/e358d132757da3e47fafaea7420803eed102b19b/s3fs/tests/test_s3fs.py#L70-L110
@pytest.fixture()
def s3_base():
    # writable local S3 system
    import shlex
    import subprocess

    try:
        # should fail since we didn't start server yet
        r = requests.get(endpoint_uri)
    except Exception:
        pass
    else:
        if r.ok:
            raise RuntimeError("moto server already up")
    if "AWS_SECRET_ACCESS_KEY" not in os.environ:
        os.environ["AWS_SECRET_ACCESS_KEY"] = "foo"
    if "AWS_ACCESS_KEY_ID" not in os.environ:
        os.environ["AWS_ACCESS_KEY_ID"] = "foo"
    proc = subprocess.Popen(
        shlex.split(f"moto_server s3 -p {port}"),
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )

    timeout = 5
    while timeout > 0:
        try:
            print("polling for moto server")
            r = requests.get(endpoint_uri)
        except Exception:
            pass
        else:
            if r.ok:
                break
        timeout -= 0.1
        time.sleep(0.1)
    try:
        print("polling done. testing if server is up")
        r = requests.get(endpoint_uri)
    except Exception as e:
        raise RuntimeError("Moto server not up") from e
    else:
        if r.ok:
            print("server up")
    yield
    print("moto done")
    proc.terminate()
    proc.wait()


def get_boto3_client():
    import boto3  # Use the boto3 included with moto since moto has strict dependencies

    return boto3.client("s3", endpoint_url=endpoint_uri)


@pytest.fixture()
def s3_app(s3_base, tmp_path):
    client = get_boto3_client()
    client.create_bucket(Bucket=test_bucket_name, ACL="public-read")

    app = create_app()
    app.config["DIAG_DIR"] = f"s3://{test_bucket_name}/"
    app.config["ENDPOINT_URL"] = endpoint_uri
    app.config["LOCAL_CACHE_PATH"] = f"{tmp_path}/cache"

    yield app


@pytest.fixture
def make_scalar_diag():
    def _make_scalar_diag(omf):
        return xr.Dataset(
            {
                "Obs_Minus_Forecast_unadjusted": omf,
            }
        )

    return _make_scalar_diag


def test_open_diagnostic(app, diag_dataset, diag_zarr):
    variable = diag.Variable.PRESSURE
    init_time = "2022-05-13T06:00"
    loop = diag.MinimLoop.ANALYSIS

    diag_zarr([variable.value], init_time, loop.value)

    with app.app_context():
        result = diag.open_diagnostic(variable, init_time, loop)

    xr.testing.assert_equal(result, diag_dataset(str(variable), init_time, str(loop)))


@pytest.mark.parametrize(
    "variable,loop,filename",
    [
        (
            diag.Variable.MOISTURE,
            diag.MinimLoop.GUESS,
            "ncdiag_conv_q_ges.nc4.2022050514",
        ),
        (
            diag.Variable.PRESSURE,
            diag.MinimLoop.ANALYSIS,
            "ncdiag_conv_ps_anl.nc4.2022050514",
        ),
        (
            diag.Variable.TEMPERATURE,
            diag.MinimLoop.ANALYSIS,
            "ncdiag_conv_t_anl.nc4.2022050514",
        ),
        (diag.Variable.WIND, diag.MinimLoop.GUESS, "ncdiag_conv_uv_ges.nc4.2022050514"),
    ],
)
def test_open_diagnostic_local(variable, loop, filename, app, make_scalar_diag):
    diag_dir = Path(app.config["DIAG_DIR"].removeprefix("file://"))
    expected = make_scalar_diag(omf=[0, -1, 2])
    expected.to_netcdf(diag_dir / filename)

    with app.app_context():
        result = diag.open_diagnostic(variable, loop)

    xr.testing.assert_equal(result, expected)


def test_open_diagnostic_local_does_not_exist(app):
    init_time = "2022-05-16T04:00"
    expected = r"No such file or directory: '.*test_diag.zarr'$"

    with app.app_context():
        with pytest.raises(FileNotFoundError, match=expected):
            diag.open_diagnostic(diag.Variable.WIND, init_time, diag.MinimLoop.GUESS)


def test_open_diagnostic_local_unknown_backend(app):
    diag_dir = Path(app.config["DIAG_DIR"].removeprefix("file://"))
    test_file = diag_dir / "ncdiag_conv_uv_ges.nc4.2022050514"
    test_file.write_bytes(b"This is not a NetCDF4 file")

    expected = (
        r"did not find a match in any of xarray's currently installed IO backends.*"
    )

    with app.app_context():
        with pytest.raises(ValueError, match=expected):
            diag.open_diagnostic(diag.Variable.WIND, diag.MinimLoop.GUESS)


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
def test_open_diagnostic_unknown_uri(uri, expected, app):
    init_time = "2022-05-16T04:00"
    app.config["DIAG_ZARR"] = uri

    with app.app_context():
        with pytest.raises(ValueError, match=expected):
            diag.open_diagnostic(diag.Variable.WIND, init_time, diag.MinimLoop.GUESS)


def test_open_diagnostic_s3_nonexistent_bucket(app):
    init_time = "2022-05-05T14:00"
    app.config["DIAG_ZARR"] = "s3://foo/test.zarr"

    expected = r"Forbidden"

    with app.app_context():
        with pytest.raises(PermissionError, match=expected):
            diag.open_diagnostic(diag.Variable.WIND, init_time, diag.MinimLoop.GUESS)


def test_open_diagnostic_s3_nonexistent_key(app):
    init_time = "2022-05-16T04:00"
    app.config["DIAG_ZARR"] = "s3://osti-modeling-dev-rtma-vis/test/no_such.zarr"
    expected = r"No such file or directory.*"

    with app.app_context():
        with pytest.raises(FileNotFoundError, match=expected):
            diag.open_diagnostic(diag.Variable.WIND, init_time, diag.MinimLoop.GUESS)


@pytest.mark.skip(reason="Moto doesn't check authentication by default")
def test_open_diagnostic_s3_unauthenticated(s3_app):
    os.unsetenv("AWS_ACCESS_KEY_ID")
    os.unsetenv("AWS_SECRET_ACCESS_KEY")

    with s3_app.app_context():
        with pytest.raises(PermissionError):
            diag.open_diagnostic(diag.Variable.WIND, diag.MinimLoop.GUESS)


def test_open_diagnostic_s3_unknown_backend(s3_app, tmp_path):
    filename = "ncdiag_conv_uv_ges.nc4.2022050514"
    test_file = tmp_path / filename
    test_file.write_bytes(b"This is not a NetCDF4 file")

    # Upload to moto
    client = get_boto3_client()
    client.upload_file(
        Bucket=test_bucket_name, Filename=str(test_file), Key=f"pytest/{filename}"
    )

    s3_app.config["DIAG_DIR"] = f"s3://{test_bucket_name}/pytest/"

    expected = (
        r"did not find a match in any of xarray's currently installed IO backends.*"
    )

    with s3_app.app_context():
        with pytest.raises(ValueError, match=expected):
            diag.open_diagnostic(diag.Variable.WIND, diag.MinimLoop.GUESS)


@pytest.mark.parametrize(
    "variable,loop,coords",
    [
        (diag.Variable.MOISTURE, diag.MinimLoop.GUESS, {}),
        (diag.Variable.PRESSURE, diag.MinimLoop.ANALYSIS, {}),
        (diag.Variable.TEMPERATURE, diag.MinimLoop.ANALYSIS, {}),
        (diag.Variable.WIND, diag.MinimLoop.GUESS, {"component": ["u", "v"]}),
    ],
)
def test_open_diagnostic_s3(
    variable, loop, coords, app, test_key_prefix, diag_zarr, diag_dataset
):
    init_time = "2022-05-05T14:00"
    zarr_file = f"s3://{test_bucket_name}{test_key_prefix}diag.zarr"
    diag_zarr([variable.value], init_time, loop.value, zarr_file)

    with app.app_context():
        app.config["DIAG_ZARR"] = zarr_file
        result = diag.open_diagnostic(variable, init_time, loop)

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
