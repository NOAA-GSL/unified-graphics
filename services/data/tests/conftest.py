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
