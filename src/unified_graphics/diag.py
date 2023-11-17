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
) -> pd.DataFrame:
    def matches(df: pd.DataFrame, filters: dict) -> bool:
        result = True

        for col_name, filter_value in filters.items():
            arr = np.array(filter_value)
            result &= (df[col_name] >= arr.min(axis=0)).all()
            result &= (df[col_name] <= arr.max(axis=0)).all()

        if "is_used" not in filters:
            result &= df["is_used"].any()

        return result

    model_config = "_".join((model, background, system, domain, frequency))

    df = pd.read_parquet(
        "/".join((uri, model_config, variable)),
        columns=[
            "obs_minus_forecast_adjusted",
            "obs_minus_forecast_unadjusted",
            "observation",
            "latitude",
            "longitude",
            "is_used",
        ],
        filters=(
            ("loop", "=", loop),
            ("initialization_time", "=", init_time),
        ),
    )

    # Group the rows of the DataFrame by nobs (effectively the observation ID) and test
    # each group against our filters. This is necessary because we use a MultiIndex for
    # vectors where the second level of the index is the vector component. If we don't
    # group the components like this, we run the risk that one component matches the
    # filters and the other doesn't, leaving us with a partial observation.
    matching_obs = [obs for _, obs in df.groupby("nobs") if matches(obs, filters)]

    # If no observations match the filters, return an empty DataFrame by masking out all
    # the values in the DataFrame using a list of repeated False values
    if len(matching_obs) < 1:
        return df[[False] * len(df)]

    # Otherwise concatenate the matching DataFrames back into a single DataFrame
    return pd.concat(matching_obs)


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
