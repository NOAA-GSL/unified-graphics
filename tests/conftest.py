import os
from typing import Optional

import alembic.command
import alembic.config

# Unused netcdf4 import to suppress a warning from numpy/xarray/netcdf4
# https://github.com/pydata/xarray/issues/7259
import netCDF4  # type: ignore # noqa: F401 # This needs to be imported before numpy
import numpy as np
import pytest
import sqlalchemy
import xarray as xr
from sqlalchemy.orm import Session

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

test_db_user = os.environ.get("TEST_DB_USER", "postgres")
test_db_pass = os.environ.get("TEST_DB_PASS", "postgres")
test_db_host = os.environ.get("TEST_DB_HOST", "localhost:5432")


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


@pytest.fixture(scope="class")
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
