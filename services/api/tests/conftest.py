import os
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from unified_graphics import create_app


@pytest.fixture(autouse=True)
def clear_aws_credentials():
    """Mocked AWS Credentials for moto

    Run this before every test to make sure we don't push to an actual S3
    instance when running tests.
    """
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def app(tmp_path):
    diag_dir = tmp_path / "data"
    diag_dir.mkdir()

    app = create_app()
    app.config["DIAG_DIR"] = str(diag_dir.as_uri())
    app.config["DIAG_ZARR"] = tmp_path / "test_diag.zarr"

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def diag_file(app):
    def factory(name: str, data: xr.Dataset):
        test_file = working_dir / name
        data.to_netcdf(test_file)
        files_created.append(test_file)

    working_dir = Path(app.config["DIAG_DIR"].removeprefix("file://"))
    files_created = []

    yield factory


@pytest.fixture
def diag_dataset():
    def factory(variable: str, initialization_time: str, loop: str, **kwargs):
        dims = [*kwargs.keys(), "nobs"]
        shape = [*map(len, kwargs.values()), 2]
        variables = [
            "observation",
            "forecast_adjusted",
            "obs_minus_forecast_adjusted",
            "forecast_unadjusted",
            "obs_minus_forecast_unadjusted",
        ]

        ds = xr.Dataset(
            {var: (dims, np.zeros(shape)) for var in variables},
            coords=dict(
                longitude=(["nobs"], np.array([90, -160], dtype=np.float64)),
                latitude=(["nobs"], np.array([22, 25], dtype=np.float64)),
                is_used=(["nobs"], np.array([1, 0], dtype=np.int8)),
                **kwargs,
            ),
            attrs={
                "name": variable,
                "loop": loop,
                "initialization_time": initialization_time,
            },
        )

        return ds

    return factory


@pytest.fixture
def diag_zarr(app, diag_dataset):
    def factory(variables: list[str], initialization_time: str, loop: str):
        with app.app_context():
            zarr_file = app.config["DIAG_ZARR"]

        for variable in variables:
            coords = {"component": ["u", "v"]} if variable == "uv" else {}

            ds = diag_dataset(variable, initialization_time, loop, **coords)
            ds.to_zarr(zarr_file, group=f"/{variable}/{initialization_time}/{loop}")

        return zarr_file

    return factory
