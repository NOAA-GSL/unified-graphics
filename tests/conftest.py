import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import alembic.command
import alembic.config

# Unused netcdf4 import to suppress a warning from numpy/xarray/netcdf4
# https://github.com/pydata/xarray/issues/7259
import netCDF4  # type: ignore # noqa: F401 # This needs to be imported before numpy
import numpy as np
import pytest
import sqlalchemy
import xarray as xr
from s3fs import S3FileSystem, S3Map  # type: ignore
from sqlalchemy.orm import Session

from unified_graphics import create_app

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

test_db_user = os.environ.get("TEST_DB_USER", "postgres")
test_db_pass = os.environ.get("TEST_DB_PASS", "postgres")
test_db_host = os.environ.get("TEST_DB_HOST", "localhost:5432")


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


@pytest.fixture(scope="session")
def db_name():
    return "test_unified_graphics"


@pytest.fixture(scope="session")
def test_db(db_name):
    autocommit_engine = sqlalchemy.create_engine(
        f"postgresql+psycopg://{test_db_user}:{test_db_pass}@{test_db_host}/postgres",
        isolation_level="AUTOCOMMIT",
    )
    with autocommit_engine.connect() as conn:
        conn.execute(sqlalchemy.text(f"DROP DATABASE IF EXISTS {db_name}"))
        conn.execute(sqlalchemy.text(f"CREATE DATABASE {db_name}"))

    url = f"postgresql+psycopg://{test_db_user}:{test_db_pass}@{test_db_host}/{db_name}"

    config = alembic.config.Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    alembic.command.upgrade(config, revision="head")

    yield url

    with autocommit_engine.connect() as conn:
        # Disconnect all users from the database we are dropping. I'm unsure why this is
        # necessary, as I think all fo the connections created for our tests should be
        # cleaned up by now.
        #
        # Copied from:
        # https://sqlalchemy-utils.readthedocs.io/en/latest/_modules/sqlalchemy_utils/functions/database.html#drop_database
        version = conn.dialect.server_version_info
        pid_column = "pid" if (version >= (9, 2)) else "procpid"
        conn.execute(
            sqlalchemy.text(
                f"""SELECT pg_terminate_backend(pg_stat_activity.{pid_column})
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{db_name}'
        AND {pid_column} <> pg_backend_pid();
        """
            )
        )
        conn.execute(sqlalchemy.text(f"DROP DATABASE {db_name}"))

    autocommit_engine.dispose()


@pytest.fixture(scope="session")
def engine(test_db):
    _engine = sqlalchemy.create_engine(test_db)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="class")
def session(engine):
    with Session(engine) as s:
        yield s
        s.rollback()


@pytest.fixture
def diag_zarr_file(tmp_path):
    return f"file://{tmp_path / 'test_diag.zarr'}"


@pytest.fixture
def app(tmp_path, diag_zarr_file, test_db):
    _app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": test_db,
            "DIAG_ZARR": diag_zarr_file,
            "DIAG_PARQUET": f"file://{tmp_path}",
        }
    )

    _app.testing = True

    yield _app


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture
def diag_file(app, tmp_path):
    def factory(
        variable: str,
        loop: str,
        init_time: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        domain: Optional[str] = None,
        frequency: Optional[str] = None,
        background: Optional[str] = None,
    ) -> Path:
        filename = f"ncdiag_conv_{variable}_{loop}.{init_time}"
        if background:
            filename += f".{background}"
        filename += ".nc4"

        if frequency:
            filename = f"{frequency}_{filename}"
        if domain:
            filename = f"{domain}_{filename}"
        if system:
            filename = f"{system}_{filename}"
        if model:
            filename = f"{model}_{filename}"

        ds = xr.Dataset(
            {
                "Forecast_adjusted": (["nobs"], np.zeros((3,))),
                "Forecast_unadjusted": (["nobs"], np.zeros((3,))),
                "Obs_Minus_Forecast_adjusted": (["nobs"], np.zeros((3,))),
                "Obs_Minus_Forecast_unadjusted": (["nobs"], np.zeros((3,))),
                "Observation": (["nobs"], np.zeros((3,))),
                "Analysis_Use_Flag": (["nobs"], np.array([1, -1, 1], dtype=np.int8)),
                "Latitude": (["nobs"], np.array([22, 23, 25], dtype=np.float64)),
                "Longitude": (["nobs"], np.array([90, 91, 200], dtype=np.float64)),
            }
        )

        diag_file = tmp_path / filename
        ds.to_netcdf(diag_file)

        return diag_file

    return factory


# FIXME: Replace diag_dataset with this fixture
@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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
def diag_parquet(tmp_path):
    def factory(
        ds: xr.Dataset,
    ) -> Path:
        parquet_file = (
            tmp_path
            / "_".join((ds.model, ds.background, ds.system, ds.domain, ds.frequency))
            / ds.name
        )
        df = ds.to_dataframe()
        df["loop"] = ds.loop
        df["initialization_time"] = ds.initialization_time

        df.to_parquet(
            parquet_file, partition_cols=["loop"], index=True, engine="pyarrow"
        )

        return parquet_file

    return factory


@pytest.fixture
def diag_zarr(diag_zarr_file, diag_dataset):
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
            zarr_file = diag_zarr_file

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
            data.to_zarr(store, group=group, consolidated=False)
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
                ds.to_zarr(store, group=group, consolidated=False)
            except Exception as e:
                raise e

        return zarr_file

    return factory
