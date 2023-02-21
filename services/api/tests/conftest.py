import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import numpy as np
import pytest
import xarray as xr
from s3fs import S3FileSystem, S3Map  # type: ignore

from unified_graphics import create_app


def pytest_addoption(parser):
    parser.addoption(
        "--runaws",
        action="store_true",
        default=False,
        help="run tests that require authentication to AWS",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "aws: mark test as requiring an authenticated connection to AWS"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runaws"):
        # If --runaws is set, there's no need to modify any of the tests
        # to mark them skipped.
        return

    # Mark any test with the aws mark as skipped because --runaws is off
    skip_aws = pytest.mark.skip(reason="use --runaws to run")
    for item in items:
        if "aws" in item.keywords:
            item.add_marker(skip_aws)


@pytest.fixture
def app(tmp_path):
    diag_dir = tmp_path / "data"
    diag_dir.mkdir()

    app = create_app()
    app.config["DIAG_DIR"] = str(diag_dir.as_uri())
    app.config["DIAG_ZARR"] = str(tmp_path / "test_diag.zarr")

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
    def factory(
        variable: str,
        initialization_time: str,
        loop: str,
        data: Optional[xr.Dataset] = None,
        **kwargs,
    ):
        dims = ["nobs", *kwargs.keys()]
        shape = [*map(len, kwargs.values()), 2]
        variables = [
            "observation",
            "forecast_adjusted",
            "obs_minus_forecast_adjusted",
            "forecast_unadjusted",
            "obs_minus_forecast_unadjusted",
        ]

        if data:
            ds = data
            ds.attrs.update(
                name=variable, loop=loop, initialization_time=initialization_time
            )
        else:
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
    def factory(
        variables: list[str],
        initialization_time: str,
        loop: str,
        zarr_file: str = "",
        data: Optional[xr.Dataset] = None,
    ):
        if not zarr_file:
            with app.app_context():
                zarr_file = app.config["DIAG_ZARR"]

        result = urlparse(zarr_file)

        if result.scheme == "s3":
            region = os.environ.get("AWS_REGION", "us-east-1")
            s3 = S3FileSystem(
                key=os.environ["AWS_ACCESS_KEY_ID"],
                secret=os.environ["AWS_SECRET_ACCESS_KEY"],
                token=os.environ["AWS_SESSION_TOKEN"],
                client_kwargs={"region_name": region},
            )

            store = S3Map(root=f"{result.netloc}{result.path}", s3=s3, check=False)
        else:
            store = result.path

        if data:
            data.to_zarr(
                store, group=f"/{data.attrs['name']}/{initialization_time}/{loop}"
            )
            return zarr_file

        for variable in variables:
            coords = {"component": ["u", "v"]} if variable == "uv" else {}

            ds = diag_dataset(variable, initialization_time, loop, **coords)
            try:
                ds.to_zarr(store, group=f"/{variable}/{initialization_time}/{loop}")
            except Exception as e:
                print(e)
                raise e

        return zarr_file

    return factory
