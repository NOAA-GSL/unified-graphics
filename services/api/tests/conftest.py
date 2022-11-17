import os
from pathlib import Path

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
