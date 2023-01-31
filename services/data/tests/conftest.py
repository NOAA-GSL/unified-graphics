from pathlib import Path

import numpy as np
import pytest
import xarray as xr


@pytest.fixture
def diag_dataset():
    def factory(
        name: str, variables: list[str], initialization_time: str, loop: str, **kwargs
    ):
        dims = [*kwargs.keys(), "nobs"]
        shape = [*map(len, kwargs.values()), 2]

        ds = xr.Dataset(
            {var: (dims, np.zeros(shape)) for var in variables},
            coords=dict(
                longitude=(["nobs"], np.array([90, -160], dtype=np.float64)),
                latitude=(["nobs"], np.array([22, 25], dtype=np.float64)),
                **kwargs,
            ),
            attrs={
                "name": name,
                "loop": loop,
                "initialization_time": initialization_time,
            },
        )

        return ds

    return factory


@pytest.fixture
def diag_zarr(tmp_path, diag_dataset):
    def factory(variables: list[str], initialization_time: str, loop: str):
        zarr_file = tmp_path / "test.zarr"

        for name in ["difference", "forecast", "observations"]:
            coords = {} if name == "observations" else {"is_adjusted": [0, 1]}

            ds = diag_dataset(name, variables, initialization_time, loop, **coords)
            ds.to_zarr(zarr_file, group=f"/{name}/{initialization_time}/{loop}")

        return zarr_file

    return factory


@pytest.fixture
def diag_file(tmp_path):
    def factory(variable: str, loop: str, init_time: str) -> Path:
        filename = f"ncdiag_conv_{variable}_{loop}.nc4.{init_time}"
        diag_file = tmp_path / filename

        ds = xr.Dataset(
            {
                "Forecast_adjusted": (["nobs"], np.zeros((2,))),
                "Forecast_unadjusted": (["nobs"], np.zeros((2,))),
                "Obs_minus_Forecast_adjusted": (["nobs"], np.zeros((2,))),
                "Obs_minus_Forecast_unadjusted": (["nobs"], np.zeros((2,))),
                "Observations": (["nobs"], np.zeros((2,))),
                "Analysis_Use_flag": (["nobs"], np.array([1, 0], dtype=np.float64)),
                "Latitude": (["nobs"], np.array([22, 25], dtype=np.float64)),
                "Longitude": (["nobs"], np.array([90, 200], dtype=np.float64)),
            }
        )

        ds.to_netcdf(diag_file)

        return diag_file

    return factory
