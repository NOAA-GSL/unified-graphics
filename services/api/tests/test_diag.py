import os
import time
from pathlib import Path

import pytest
import requests
import xarray as xr

from unified_graphics import create_app, diag

# Global resources for s3
test_bucket_name = "test"
port = 5555
endpoint_uri = f"http://127.0.0.1:{port}/"


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
    expected = r"No such file: '.*ncdiag_conv_uv_ges.nc4.2022050514'$"

    with app.app_context():
        with pytest.raises(FileNotFoundError, match=expected):
            diag.open_diagnostic(diag.Variable.WIND, diag.MinimLoop.GUESS)


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


def test_open_diagnostic_unknown_uri(app):
    app.config["DIAG_DIR"] = "foo://an/unknown/uri"

    expected = r"Unknown file URI: 'foo://an/unknown/uri'"

    with app.app_context():
        with pytest.raises(FileNotFoundError, match=expected):
            diag.open_diagnostic(diag.Variable.WIND, diag.MinimLoop.GUESS)


def test_open_diagnostic_s3_nonexistent_bucket(s3_app):
    s3_app.config["DIAG_DIR"] = "s3://foo/"

    expected = r"The specified bucket does not exist"

    with s3_app.app_context():
        with pytest.raises(FileNotFoundError, match=expected):
            diag.open_diagnostic(diag.Variable.WIND, diag.MinimLoop.GUESS)


def test_open_diagnostic_s3_nonexistent_key(s3_app):
    expected = r"The specified key does not exist"

    with s3_app.app_context():
        with pytest.raises(FileNotFoundError, match=expected):
            diag.open_diagnostic(diag.Variable.WIND, diag.MinimLoop.GUESS)


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
def test_open_diagnostic_s3(
    variable, loop, filename, s3_app, make_scalar_diag, tmp_path
):
    # Write the netcdf file to disk before uploading
    # Using a fileobj instead of writing to disk would be cleaner but requires using
    # the scipy engine
    expected = make_scalar_diag(omf=[0, -1, 2])
    expected.to_netcdf(tmp_path / filename)

    client = get_boto3_client()
    client.upload_file(
        Bucket=test_bucket_name,
        Filename=str(tmp_path / filename),
        Key=f"pytest/{filename}",
    )

    s3_app.config["DIAG_DIR"] = f"s3://{test_bucket_name}/pytest/"

    with s3_app.app_context():
        result = diag.open_diagnostic(variable, loop)

    xr.testing.assert_equal(result, expected)
