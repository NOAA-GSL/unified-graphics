from collections import namedtuple
from pathlib import Path
from typing import Union

import xarray as xr

DiagData = namedtuple("DiagData", "observations forecast difference")
DiagMeta = namedtuple("DiagMeta", "variable loop initialization_time")


def parse_diag_filename(filename: str) -> DiagMeta:
    name, _, init_time = filename.split(".")
    variable, loop = name.split("_")[2:]

    return DiagMeta(variable, loop, init_time)


def load(path: Union[Path, str]) -> DiagData:
    variable, loop, init_time = parse_diag_filename(Path(path).name)

    ds = xr.open_dataset(path)

    observations = xr.Dataset({variable: (["nobs"], ds["Observations"].data)})
    forecast = xr.Dataset(
        {
            variable: (
                ["is_adjusted", "nobs"],
                xr.concat(
                    [
                        ds["Forecast_unadjusted"].expand_dims({"is_adjusted": [0]}),
                        ds["Forecast_adjusted"].expand_dims({"is_adjusted": [1]}),
                    ],
                    dim="is_adjusted",
                ).data,
            )
        },
        coords={"is_adjusted": [0, 1]},
        attrs={"name": "forecast", "loop": loop, "initialization_time": init_time},
    )
    difference = xr.Dataset(
        {
            variable: (
                ["is_adjusted", "nobs"],
                xr.concat(
                    [
                        ds["Obs_minus_Forecast_unadjusted"].expand_dims(
                            {"is_adjusted": [0]}
                        ),
                        ds["Obs_minus_Forecast_adjusted"].expand_dims(
                            {"is_adjusted": [1]}
                        ),
                    ],
                    dim="is_adjusted",
                ).data,
            )
        },
        coords={"is_adjusted": [0, 1]},
        attrs={"name": "difference", "loop": loop, "initialization_time": init_time},
    )

    return DiagData(observations, forecast, difference)


def save(path: Union[Path, str], *args: xr.Dataset):
    """Write one or more xarray Datasets to a Zarr at `path`

    The `name` and `loop` variables are used along with the
    `initialization_time` (non-dimension) coordinates to define the group to
    which the Dataset is written in the Zarr.

    Parameters
    ----------
    path : Path
        The path to the location of the Zarr
    """
    for ds in args:
        group = f"{ds.name}/{ds.initialization_time}/{ds.loop}"
        ds.to_zarr(path, group=group, mode="a")
