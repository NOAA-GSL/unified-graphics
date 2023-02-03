import re
from collections import namedtuple
from pathlib import Path
from typing import Union

import xarray as xr

DiagMeta = namedtuple("DiagMeta", "variables loop initialization_time")

diag_filename_regex = re.compile(
    (
        r".*?(?:nc)?diag_(?:conv_)?(ps|q|t|uv)_(anl|ges|\d+)\..*?"
        r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})?.*"
    )
)


def parse_diag_filename(filename: str) -> DiagMeta:
    """Parse the variable, loop, and initialization time from a diag file name

    The filename is expected to be of the form
    X_Y_VARIABLE_LOOP.EXT.YYYYMMDDHH. `X`, `Y`, and `EXT` aren't used, so it
    doesn't really matter what those are, as long as they're present in the
    file name.

    Parameters
    ----------
    filename : str
        The filename for a NetCDF diagnostics file

    Returns
    -------
    DiagMeta
        A DiagMeta named tuple containing the variable, loop, and initialization time
    """
    filename_match = diag_filename_regex.match(filename)
    if not filename_match:
        raise ValueError(f"Invalid diagnostics filename: {filename}")

    variable, loop, year, month, day, hour, minute = filename_match.groups()
    # A uv diag file (wind) actually contains two variables -- u and v -- for
    # the vectors
    variables = list(variable) if variable == "uv" else [variable]
    init_time = f"{year}-{month}-{day}T{hour}"
    if minute:
        init_time += ":" + minute

    return DiagMeta(variables, loop, init_time)


def get_adjusted(ds: xr.Dataset):
    def fn(variable: str) -> list[str]:
        if variable in ds:
            return [variable]

        return [f"{variable}_adjusted", f"{variable}_unadjusted"]

    return fn


def get_data_array(
    dataset: xr.Dataset, variable: str, components: list[str] = []
) -> xr.DataArray:
    if not components:
        return dataset[variable]

    key = f"{components[0]}_{variable}"
    da = dataset[key].expand_dims({"component": [components[0]]}, axis=1)
    for c in components[1:]:
        key = f"{c}_{variable}"
        da = xr.concat(
            [
                da,
                dataset[key].expand_dims({"component": [c]}, axis=1),
            ],
            dim="component",
        )

    return da


def load(path: Path) -> xr.Dataset:
    """Load a NetCDF diag file into xarray Datasets for observations,
    forecasts, and differences

    This function transforms the data in a diag file into a format that uses
    many of the variables from the NetCDF file as coordinates.

    Parameters
    ----------
    path : Path, str
        The path to the NetCDF diag file

    Returns
    -------
    xarray.Dataset
        A transformed xarray Dataset containing the observation, forecast
        adjusted/unadjusted, and difference adjusted/unadjusted variables from
        the diag file.
    """
    diag_variables, loop, init_time = parse_diag_filename(path.name)

    ds = xr.open_dataset(path)

    coords = {
        "latitude": (["nobs"], ds["Latitude"].data),
        "longitude": (
            ["nobs"],
            xr.where(
                ds["Longitude"] > 180, ds["Longitude"] - 360, ds["Longitude"]
            ).data,
        ),
        "is_used": (["nobs"], (ds["Analysis_Use_Flag"] == 1).data),
    }

    components = []
    if len(diag_variables) > 1:
        coords["component"] = diag_variables
        components = diag_variables

    variables = [
        "Observation",
        "Forecast_unadjusted",
        "Forecast_adjusted",
        "Obs_Minus_Forecast_unadjusted",
        "Obs_Minus_Forecast_adjusted",
    ]

    transformed = xr.Dataset(
        {name.lower(): get_data_array(ds, name, components) for name in variables},
        coords=coords,
        attrs={
            "name": "".join(diag_variables),
            "loop": loop,
            "initialization_time": init_time,
        },
    )

    return transformed


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
