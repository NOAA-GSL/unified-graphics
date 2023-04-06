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


# FIXME: Replace diag_dataset with this fixture
@pytest.fixture
def test_dataset():
    def factory(
        *,
        model: str = "RTMA",
        system: str = "WCOSS",
        domain: str = "CONUS",
        background: str = "HRRR",
        frequency: str = "REALTIME",
        initialization_time: str = "2022-05-16T04:00",
        variable: str = "ps",
        loop: str = "ges",
        longitude: list[float] = [90, 91],
        latitude: list[float] = [22, 23],
        is_used: list[int] = [1, 0],
        observation: list[float] = [1, 0],
        forecast_unadjusted: list[float] = [0, 1],
        forecast_adjusted: Optional[list[float]] = None,
        **kwargs,
    ):
        assert len(observation) == len(forecast_unadjusted)
        if forecast_adjusted:
            assert len(forecast_adjusted) == len(forecast_unadjusted)

        dims = ["nobs", *kwargs.keys()]

        obs = np.array(observation, dtype=np.float64)
        unadj = np.array(forecast_unadjusted, dtype=np.float64)
        adj = np.array(forecast_adjusted or forecast_unadjusted, dtype=np.float64)

        return xr.Dataset(
            {
                "observation": (dims, obs),
                "forecast_unadjusted": (dims, unadj),
                "forecast_adjusted": (dims, adj),
                "obs_minus_forecast_unadjusted": (dims, obs - unadj),
                "obs_minus_forecast_adjusted": (dims, obs - adj),
            },
            coords=dict(
                longitude=(["nobs"], np.array(longitude, dtype=np.float64)),
                latitude=(["nobs"], np.array(latitude, dtype=np.float64)),
                is_used=(["nobs"], np.array(is_used, dtype=np.int8)),
                **kwargs,
            ),
            attrs={
                "name": variable,
                "loop": loop,
                "initialization_time": initialization_time,
                "model": model,
                "system": system,
                "domain": domain,
                "frequency": frequency,
                "background": background,
            },
        )

    return factory


@pytest.fixture
def diag_dataset():
    def factory(
        variable: str,
        initialization_time: str,
        loop: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        domain: Optional[str] = None,
        frequency: Optional[str] = None,
        background: Optional[str] = None,
        data: Optional[xr.Dataset] = None,
        **kwargs,
    ):
        dims = ["nobs", *kwargs.keys()]
        shape = [3, *map(len, kwargs.values())]
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
                    longitude=(["nobs"], np.array([90, 91, -160], dtype=np.float64)),
                    latitude=(["nobs"], np.array([22, 23, 25], dtype=np.float64)),
                    is_used=(["nobs"], np.array([1, 0, 1], dtype=np.int8)),
                    **kwargs,
                ),
                attrs={
                    "name": variable,
                    "loop": loop,
                    "initialization_time": initialization_time,
                    "model": model or "Unknown",
                    "system": system or "Unknown",
                    "domain": domain or "Unknown",
                    "frequency": frequency or "Unknown",
                    "background": background or "Unknown",
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
        model: Optional[str] = "RTMA",
        system: Optional[str] = "WCOSS",
        domain: Optional[str] = "CONUS",
        frequency: Optional[str] = "REALTIME",
        background: Optional[str] = "HRRR",
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
            group = (
                f"/{data.model}/{data.system}/{data.domain}/{data.background}"
                f"/{data.frequency}/{data.attrs['name']}/{initialization_time}/{loop}"
            )
            data.to_zarr(store, group=group)
            return zarr_file

        for variable in variables:
            coords = {"component": ["u", "v"]} if variable == "uv" else {}

            ds = diag_dataset(
                variable,
                initialization_time,
                loop,
                model,
                system,
                domain,
                frequency,
                background,
                **coords,
            )
            try:
                group = (
                    f"/{ds.model}/{ds.system}/{ds.domain}/{ds.background}"
                    f"/{ds.frequency}/{variable}/{initialization_time}/{loop}"
                )
                ds.to_zarr(store, group=group)
            except Exception as e:
                raise e

        return zarr_file

    return factory
