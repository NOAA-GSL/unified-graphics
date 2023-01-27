import numpy as np
import pytest
import xarray as xr


@pytest.fixture
def diag_dataset():
    def factory(
        name: str, variables: list[str], initialization_time: str, loop: str, **kwargs
    ):
        dims = [*kwargs.keys(), "nobs"]
        shape = [*map(len, kwargs.values()), 1]

        ds = xr.Dataset(
            {var: (dims, np.zeros(shape)) for var in variables},
            coords=kwargs,
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
