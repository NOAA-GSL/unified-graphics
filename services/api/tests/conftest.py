from pathlib import Path

import pytest
import xarray as xr

from unified_graphics import create_app


@pytest.fixture
def app(tmp_path):
    diag_dir = tmp_path / "data"
    diag_dir.mkdir()

    app = create_app()
    app.config["DIAG_DIR"] = str(diag_dir)

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

    working_dir = Path(app.config["DIAG_DIR"])
    files_created = []

    yield factory
