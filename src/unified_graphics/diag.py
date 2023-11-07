import os
from collections import namedtuple
from enum import Enum
from typing import Union
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import sqlalchemy as sa
import xarray as xr
import zarr  # type: ignore
from s3fs import S3FileSystem, S3Map  # type: ignore
from werkzeug.datastructures import MultiDict
from xarray.core.dataset import Dataset

from .models import Analysis, WeatherModel


class MinimLoop(Enum):
    GUESS = "ges"
    ANALYSIS = "anl"


class Variable(Enum):
    MOISTURE = "q"
    PRESSURE = "ps"
    TEMPERATURE = "t"
    WIND = "uv"


ModelMetadata = namedtuple(
    "ModelMetadata",
    (
        "model_list system_list domain_list background_list frequency_list "
        "variable_list init_time_list"
    ),
)


def get_model_metadata(session) -> ModelMetadata:
    model_list = session.scalars(
        sa.select(WeatherModel.name)
        .where(WeatherModel.analysis_list.any())
        .distinct()
        .order_by(WeatherModel.name)
    ).all()
    system_list = session.scalars(
        sa.select(Analysis.system).distinct().order_by(Analysis.system)
    ).all()
    domain_list = session.scalars(
        sa.select(Analysis.domain).distinct().order_by(Analysis.domain)
    ).all()
    frequency_list = session.scalars(
        sa.select(Analysis.frequency).distinct().order_by(Analysis.frequency)
    ).all()

    bg_subq = (
        sa.select(WeatherModel.background_id)
        .where(WeatherModel.background_id.isnot(None))
        .distinct()
        .subquery("bg_model")
    )
    background_list = session.scalars(
        sa.select(WeatherModel.name)
        .join(bg_subq, bg_subq.c.background_id == WeatherModel.id)
        .distinct()
        .order_by(WeatherModel.name)
    ).all()

    init_time_list = [
        t.isoformat(timespec="minutes")
        for t in session.scalars(
            sa.select(Analysis.time).distinct().order_by(Analysis.time)
        ).all()
    ]

    variable_list = ["ps", "q", "t", "uv"]

    return ModelMetadata(
        model_list,
        system_list,
        domain_list,
        background_list,
        frequency_list,
        variable_list,
        init_time_list,
    )


def get_store(url: str) -> Union[str, S3Map]:
    result = urlparse(url)
    if result.scheme in ["", "file"]:
        return result.path

    if result.scheme != "s3":
        raise ValueError(f"Unsupported protocol '{result.scheme}' for URI: '{url}'")

    region = os.environ.get("AWS_REGION", "us-east-1")
    s3 = S3FileSystem(
        key=os.environ.get("AWS_ACCESS_KEY_ID"),
        secret=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        token=os.environ.get("AWS_SESSION_TOKEN"),
        client_kwargs={"region_name": region},
    )

    return S3Map(root=f"{result.netloc}{result.path}", s3=s3, check=False)


def open_diagnostic(
    diag_zarr: str,
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    variable: Variable,
    initialization_time: str,
    loop: MinimLoop,
) -> xr.Dataset:
    store = get_store(diag_zarr)
    group = (
        f"/{model}/{system}/{domain}/{background}/{frequency}"
        f"/{variable.value}/{initialization_time}/{loop.value}"
    )
    return xr.open_zarr(store, group=group, consolidated=False)


def parse_filter_value(value):
    if value == "true":
        return 1

    if value == "false":
        return 0

    try:
        return float(value)
    except ValueError:
        return value


# TODO: Refactor to a class
# I think this might belong in a different module. It could be a class or set of classes
# that represent different filters that can be added together into a filtering pipeline
def get_bounds(filters: MultiDict):
    for coord, value in filters.items():
        extent = np.array(
            [
                [parse_filter_value(digit) for digit in pair.split(",")]
                for pair in value.split("::")
            ]
        )
        yield coord, extent.min(axis=0), extent.max(axis=0)


def apply_filters(dataset: xr.Dataset, filters: MultiDict) -> Dataset:
    for coord, lower, upper in get_bounds(filters):
        data_array = dataset[coord]
        dataset = dataset.where((data_array >= lower) & (data_array <= upper)).dropna(
            dim="nobs"
        )

    # If the is_used filter is not passed, our default behavior is to include only used
    # observations.
    if "is_used" not in filters:
        dataset = dataset.where(dataset["is_used"]).dropna(dim="nobs")

    return dataset


def scalar(
    diag_zarr: str,
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    variable: Variable,
    initialization_time: str,
    loop: MinimLoop,
    filters: MultiDict,
) -> pd.DataFrame:
    data = open_diagnostic(
        diag_zarr,
        model,
        system,
        domain,
        background,
        frequency,
        variable,
        initialization_time,
        loop,
    )
    data = apply_filters(data, filters)

    return data.to_dataframe()


def temperature(
    diag_zarr: str,
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    initialization_time: str,
    loop: MinimLoop,
    filters: MultiDict,
) -> pd.DataFrame:
    return scalar(
        diag_zarr,
        model,
        system,
        domain,
        background,
        frequency,
        Variable.TEMPERATURE,
        initialization_time,
        loop,
        filters,
    )


def moisture(
    diag_zarr: str,
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    initialization_time: str,
    loop: MinimLoop,
    filters: MultiDict,
) -> pd.DataFrame:
    return scalar(
        diag_zarr,
        model,
        system,
        domain,
        background,
        frequency,
        Variable.MOISTURE,
        initialization_time,
        loop,
        filters,
    )


def pressure(
    diag_zarr: str,
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    initialization_time: str,
    loop: MinimLoop,
    filters: MultiDict,
) -> pd.DataFrame:
    return scalar(
        diag_zarr,
        model,
        system,
        domain,
        background,
        frequency,
        Variable.PRESSURE,
        initialization_time,
        loop,
        filters,
    )


def wind(
    diag_zarr: str,
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    initialization_time: str,
    loop: MinimLoop,
    filters: MultiDict,
) -> pd.DataFrame | pd.Series:
    data = open_diagnostic(
        diag_zarr,
        model,
        system,
        domain,
        background,
        frequency,
        Variable.WIND,
        initialization_time,
        loop,
    )

    data = apply_filters(data, filters)

    return data.to_dataframe()


def magnitude(dataset: pd.DataFrame) -> pd.DataFrame:
    return dataset.groupby(level=0).aggregate(
        {
            "obs_minus_forecast_adjusted": np.linalg.norm,
            "obs_minus_forecast_unadjusted": np.linalg.norm,
            "observation": np.linalg.norm,
            "longitude": "first",
            "latitude": "first",
        }
    )


def get_model_run_list(
    diag_zarr: str,
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    variable: Variable,
):
    store = get_store(diag_zarr)
    path = "/".join([model, system, domain, background, frequency, variable.value])
    with zarr.open_group(store, mode="r", path=path) as group:
        return group.group_keys()


def history(
    parquet_path: str,
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    variable: Variable,
    loop: MinimLoop,
    filters: MultiDict,
) -> pd.DataFrame:
    parquet_file = os.path.join(
        parquet_path,
        "_".join((model, background, system, domain, frequency)),
        variable.value,
    )

    df = pd.read_parquet(
        parquet_file,
        columns=["initialization_time", "obs_minus_forecast_unadjusted"],
        filters=(("loop", "=", loop.value), ("is_used", "=", True)),
    )

    if df.empty:
        return df

    df = (
        df.sort_values("initialization_time")
        .groupby("initialization_time")
        .describe()
        .droplevel(0, axis=1)  # Drop a level from the columns created by the groupby
        .reset_index()
    )

    return df[["initialization_time", "min", "max", "mean", "count"]]
