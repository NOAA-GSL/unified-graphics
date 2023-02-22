from pathlib import Path

# Unused netcdf4 import to suppress a warning from numpy/xarray/netcdf4
# https://github.com/pydata/xarray/issues/7259
import netCDF4  # type: ignore # noqa: F401 # This needs to be imported before numpy
import numpy as np
import pytest
import xarray as xr


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
def diag_zarr(tmp_path, diag_dataset):
    def factory(variables: list[str], initialization_time: str, loop: str):
        zarr_file = tmp_path / "test.zarr"

        for variable in variables:
            coords = {"component": ["u", "v"]} if variable == "uv" else {}

            ds = diag_dataset(variable, initialization_time, loop, **coords)
            ds.to_zarr(zarr_file, group=f"/{variable}/{initialization_time}/{loop}")

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
                "Obs_Minus_Forecast_adjusted": (["nobs"], np.zeros((2,))),
                "Obs_Minus_Forecast_unadjusted": (["nobs"], np.zeros((2,))),
                "Observation": (["nobs"], np.zeros((2,))),
                "Analysis_Use_Flag": (["nobs"], np.array([1, -1], dtype=np.int8)),
                "Latitude": (["nobs"], np.array([22, 25], dtype=np.float64)),
                "Longitude": (["nobs"], np.array([90, 200], dtype=np.float64)),
            }
        )

        ds.to_netcdf(diag_file)

        return diag_file

    return factory
