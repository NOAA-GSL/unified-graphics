from collections import namedtuple
from pathlib import Path
from typing import Union

import xarray as xr

DiagData = namedtuple("DiagData", "observations forecast difference")
DiagMeta = namedtuple("DiagMeta", "variables loop initialization_time")


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
    try:
        name, _, init_time = filename.split(".")
        variable, loop = name.split("_")[2:]
    except ValueError:
        raise ValueError(f"Invalid diagnostics filename: '{filename}'")

    if len(init_time) != 10:
        raise ValueError(f"Unrecognized date format in filename: {filename}")

    year = init_time[:4]
    month = init_time[4:6]
    day = init_time[6:8]
    hour = init_time[8:10]

    variables = list(variable) if variable == "uv" else [variable]

    return DiagMeta(variables, loop, f"{year}-{month}-{day}T{hour}")


def get_data_array(
    dataset: xr.Dataset, variable: str, variable_type: str, *args: str
) -> xr.DataArray:
    """Look for a variable in a dataset

    Vector variables (wind) have two separate variables in the NetCDF for any
    given data type. Instead of Observations, for example, they have
    Observations_u and Observations_v. This function tries two different
    formulations of the Dataset variable name, first without the model
    variable, and then with. If neither is found, a `KeyError` is raised.
    """
    name = "_".join([variable_type, *args])
    if name in dataset:
        return dataset[name]

    name = "_".join([variable_type, variable, *args])
    if name in dataset:
        return dataset[name]

    raise KeyError(f"Variable for '{name}' not found")


def get_variable_with_adjustment(
    dataset: xr.Dataset, variable: str, variable_type: str
) -> xr.DataArray:
    """Combine _adjusted and _unadjusted variables into a single DataArray"""
    adjusted = get_data_array(dataset, variable, variable_type, "adjusted")
    adjusted = adjusted.expand_dims({"is_adjusted": [1]})

    unadjusted = get_data_array(dataset, variable, variable_type, "unadjusted")
    unadjusted = unadjusted.expand_dims({"is_adjusted": [0]})

    da = xr.concat([unadjusted, adjusted], dim="is_adjusted")

    return xr.DataArray(
        da.data,
        dims=["is_adjusted", "nobs"],
        coords={"is_adjusted": [0, 1]},
        attrs={"name": variable},
    )


def get_observations(dataset: xr.Dataset, variable: str) -> xr.DataArray:
    """Return the DataArray for this variable's Observations column"""
    da = get_data_array(dataset, variable, "Observations")
    return xr.DataArray(da.data, dims=["nobs"], attrs={"name": variable})


def get_forecast(dataset: xr.Dataset, variable: str) -> xr.DataArray:
    """Return the DataArray for this variable's Forecast column

    Combines the _adjusted and _unadjusted variables into a single variable
    with a boolean `is_adjusted` dimension.
    """
    return get_variable_with_adjustment(dataset, variable, "Forecast")


def get_difference(dataset: xr.Dataset, variable: str) -> xr.DataArray:
    """Return the DataArray for this variable's Obs_minus_Forecast column

    Combines the _adjusted and _unadjusted variables into a single variable
    with a boolean `is_adjusted` dimension.
    """
    return get_variable_with_adjustment(dataset, variable, "Obs_minus_Forecast")


def load(path: Path) -> DiagData:
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
    DiagData
        A named tuple containing an xarray Dataset for the observations,
        forecast, and difference (observation - forecast) in the diag file.
    """

    variables, loop, init_time = parse_diag_filename(path.name)

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

    observations = xr.Dataset(
        {variable: get_observations(ds, variable) for variable in variables},
        coords=coords,
        attrs={"name": "observations", "loop": loop, "initialization_time": init_time},
    )
    forecast = xr.Dataset(
        {variable: get_forecast(ds, variable) for variable in variables},
        coords=coords,
        attrs={"name": "forecast", "loop": loop, "initialization_time": init_time},
    )
    difference = xr.Dataset(
        {variable: get_difference(ds, variable) for variable in variables},
        coords=coords,
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
