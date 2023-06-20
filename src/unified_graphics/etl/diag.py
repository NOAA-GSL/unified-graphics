import logging
import re
from collections import namedtuple
from datetime import datetime
from pathlib import Path
from typing import Union

import pandas as pd
import xarray as xr
from sqlalchemy import select
from sqlalchemy.orm import Session

from unified_graphics.models import Analysis, WeatherModel

logger = logging.getLogger(__name__)

DiagMeta = namedtuple(
    "DiagMeta",
    "variables loop initialization_time model system domain frequency background",
)

diag_filename_regex = re.compile(
    (
        # Ignore optional UUID and capture model, system, domain, and frequency
        r"(?:[a-z0-9][a-z0-9-]*-)?(?:(\w+)_)?"
        # Capture variable and loop
        r"(?:nc)?diag_(?:conv_)?(ps|q|t|uv)_(anl|ges|\d+)\..*?"
        # capture initialization time and background
        r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})?(?:\.(\w+))?\.nc4"
    )
)


def parse_diag_filename(filename: str) -> DiagMeta:
    """Parse the variable, loop, and initialization time from a diag file name

    The filename is expected to be of the form

    diag_VARIABLE_LOOP.YYYYMMDDHHmm.BACKGROUND.nc4

    `diag` may also be `ncdiag`, and the string `conv_` may come before `VARIABLE` or
    may be omitted. `BACKGROUND` is also optional, as are the minutes (`mm`) in the
    initialization time.

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

    (
        meta,
        variable,
        loop,
        year,
        month,
        day,
        hour,
        minute,
        background,
    ) = filename_match.groups()

    if meta:
        model, system, domain, frequency = (meta.split("_") + [None] * 4)[:4]
    else:
        model, system, domain, frequency = [None] * 4

    # A uv diag file (wind) actually contains two variables -- u and v -- for
    # the vectors
    variables = list(variable) if variable == "uv" else [variable]
    init_time = f"{year}-{month}-{day}T{hour}"
    if minute:
        init_time += ":" + minute
    else:
        init_time += ":00"

    return DiagMeta(
        variables, loop, init_time, model, system, domain, frequency, background
    )


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


def compute_forecast(
    suffix: str, ds: xr.Dataset, component_list: list[str] = []
) -> xr.Dataset:
    if component_list:
        key_list = [
            (
                f"{component}_Observation",
                f"{component}_Obs_Minus_Forecast_{suffix}",
                f"{component}_Forecast_{suffix}",
            )
            for component in component_list
        ]
    else:
        key_list = [
            ("Observation", f"Obs_Minus_Forecast_{suffix}", f"Forecast_{suffix}")
        ]

    for obs_key, delta_key, forecast_key in key_list:
        obs = ds[obs_key]
        delta = ds[delta_key]
        forecast = obs - delta
        ds[forecast_key] = forecast

    return ds


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
    (
        diag_variables,
        loop,
        init_time,
        model,
        system,
        domain,
        frequency,
        background,
    ) = parse_diag_filename(path.name)

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

    # Some diag files do not include the forecast variables, so before we
    # transform the input, we compute the forecast if it's missing.
    if "Forecast_adjusted" not in ds:
        compute_forecast("adjusted", ds, components)
    if "Forecast_unadjusted" not in ds:
        compute_forecast("unadjusted", ds, components)

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
            "model": model or "Unknown",
            "system": system or "Unknown",
            "domain": domain or "Unknown",
            "frequency": frequency or "Unknown",
            "background": background or "Unknown",
        },
    )

    return transformed


def prep_dataframe(ds: xr.Dataset) -> pd.DataFrame:
    """Prepare a diagnostic dataset for storing in a Parquet file

    Creates a pandas DataFrame from `ds` and cleans the string columns.

    Parameters
    ----------
    ds : xarray.Dataset
        The Dataset to convert to a DataFrame
    """
    df = ds.to_dataframe()

    df["loop"] = ds.loop
    df["initialization_time"] = datetime.fromisoformat(ds.initialization_time)

    # FIXME: Clean the string columns Station_ID, Provider_Name, Subprovider_Name

    return df


def save(session: Session, path: Union[Path, str], *args: xr.Dataset):
    """Write one or more xarray Datasets to a Zarr at `path`

    The `name` and `loop` variables are used along with the
    `initialization_time` (non-dimension) coordinates to define the group to
    which the Dataset is written in the Zarr.

    Parameters
    ----------
    path : Path
        The path to the location of the Zarr
    """
    logger.info("Started saving dataset to Zarr and the DB")
    for ds in args:
        model = ds.model or "Unknown"
        system = ds.system or "Unknown"
        domain = ds.domain or "Unknown"
        background = ds.background or "Unknown"
        frequency = ds.frequency or "Unknown"
        group = (
            f"{model}/{system}/{domain}/{background}/{frequency}/"
            f"{ds.name}/{ds.initialization_time}/{ds.loop}"
        )

        analysis = None
        wx_model = None
        bg = session.scalar(
            select(WeatherModel).where(
                WeatherModel.name == background,
                WeatherModel.background_id.is_(None),
            )
        )

        if bg:
            wx_model = session.scalar(
                select(WeatherModel).where(
                    WeatherModel.name == model, WeatherModel.background_id == bg.id
                )
            )
        else:
            bg = WeatherModel(name=background)

        if not wx_model:
            wx_model = WeatherModel(name=model)
            wx_model.background = bg
            session.add(wx_model)

        if wx_model.id:
            analysis = session.scalar(
                select(Analysis).where(
                    Analysis.time == datetime.fromisoformat(ds.initialization_time),
                    Analysis.system == system,
                    Analysis.frequency == frequency,
                    Analysis.domain == domain,
                    Analysis.model_id == wx_model.id,
                )
            )

        if not analysis:
            analysis = Analysis(
                time=datetime.fromisoformat(ds.initialization_time),
                system=system,
                frequency=frequency,
                domain=domain,
            )
            analysis.model = wx_model
            session.add(analysis)

        logger.info(f"Saving dataset to Zarr at: {path}")
        ds.to_zarr(path, group=group, mode="a", consolidated=False)

        logger.info("Saving dataset to Database")
        session.commit()

        logger.info("Done saving dataset")
