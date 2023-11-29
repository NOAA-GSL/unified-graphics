import os
from collections import namedtuple
from datetime import datetime, timedelta
from enum import Enum

import numpy as np
import pandas as pd
import sqlalchemy as sa
from werkzeug.datastructures import MultiDict

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


def diag_observations(
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    variable: str,
    init_time: datetime,
    loop: str,
    uri: str,
    filters: dict = {},
) -> pd.DataFrame | pd.Series:
    model_config = "_".join((model, background, system, domain, frequency))

    is_used = filters.pop("is_used", True)
    parquet_filters = [
        ("loop", "=", loop),
        ("initialization_time", "=", init_time),
    ]

    if isinstance(is_used, bool):
        parquet_filters.append(("is_used", "=", is_used))

    df = pd.read_parquet(
        os.path.join((uri, model_config, variable)),
        columns=[
            "obs_minus_forecast_adjusted",
            "obs_minus_forecast_unadjusted",
            "observation",
            "latitude",
            "longitude",
            "is_used",
        ],
        filters=parquet_filters,
    )

    # To apply the filters, we need the vector components in the columns, not
    # the rows.
    # FIXME: We should consider changing how we store the vector data so we
    # don't have to unstack it every time.
    if "component" in df.index.names:
        # FIXME: Specifically unstack the component level of the index because
        # I'm seeing some data where the index is (component, nobs) instead of
        # (nobs, component)
        df = df.unstack("component")  # type: ignore

    # Iterate over each filter and apply it
    for col_name, filter_value in filters.items():
        arr = np.array(filter_value)

        # Boolean mask for the rows in the data that are within the range
        # specified by the filter
        mask = (df[col_name] >= arr.min(axis=0)) & (df[col_name] <= arr.max(axis=0))

        # In the event of a vector variable, we will have a DataFrame mask
        # instead of a Series, which we need to flatten to a series which
        # evaluates to True only when every column in the frame is True. If any
        # column is False, this row should be excluded from the data
        if len(mask.shape) > 1:
            mask = mask.all(axis="columns")

        # Apply the mask
        df = df[mask]

    return df


def history(
    parquet_path: str,
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    variable: Variable,
    loop: MinimLoop,
    initialization_time: datetime,
    filters: MultiDict,
) -> pd.DataFrame:
    parquet_file = os.path.join(
        parquet_path,
        "_".join((model, background, system, domain, frequency)),
        variable.value,
    )

    start = initialization_time - timedelta(days=2)
    df = pd.read_parquet(
        parquet_file,
        columns=["initialization_time", "obs_minus_forecast_unadjusted"],
        filters=(
            ("loop", "=", loop.value),
            ("is_used", "=", True),
            ("initialization_time", ">=", start),
            ("initialization_time", "<=", initialization_time),
        ),
    )

    if df.empty:
        return df

    df = (
        df.sort_values("initialization_time")
        .groupby("initialization_time")
        .describe()
        .droplevel(0, axis=1)  # Drop a level from the columns created by the groupby
        .reset_index()
    )[["initialization_time", "min", "25%", "50%", "75%", "max", "mean", "count"]]

    return df
