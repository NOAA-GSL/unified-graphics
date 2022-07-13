from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
import os

from flask import current_app
import numpy as np
import xarray as xr


class MinimLoop(Enum):
    GUESS = "ges"
    ANALYSIS = "anl"


class Variable(Enum):
    MOISTURE = "q"
    PRESSURE = "p"
    TEMPERATURE = "t"
    WIND = "uv"


@dataclass
class VectorVariable:
    direction: List[float]
    magnitude: List[float]

    @classmethod
    def from_vectors(cls, u: xr.DataArray, v: xr.DataArray) -> "VectorVariable":
        return cls(direction=[], magnitude=[])


@dataclass
class VectorDiag:
    observation: VectorVariable
    forecast: VectorVariable


def get_filepath(loop) -> str:
    return os.path.join(
        current_app.config["DIAG_DIR"], f"ncdiag_conv_t_{loop.value}.nc4.2022050514"
    )


def get_diagnostics(loop: MinimLoop) -> Dict:
    diag_file = get_filepath(loop)
    ds = xr.open_dataset(diag_file)
    obs_minus_fcast = ds["Obs_Minus_Forecast_adjusted"].values

    obs_count = len(obs_minus_fcast)
    mean = float(np.mean(obs_minus_fcast))
    std = float(np.std(obs_minus_fcast))
    counts, bins = np.histogram(obs_minus_fcast, bins="auto")

    distribution = [
        {"lower": float(bins[idx]), "upper": float(bins[idx + 1]), "value": int(count)}
        for idx, count in enumerate(counts)
    ]

    return {
        "bins": distribution,
        "observations": obs_count,
        "std": std,
        "mean": mean,
    }


def open_diagnostic(variable: Variable, loop: MinimLoop) -> Optional[xr.Dataset]:
    filename = f"ncdiag_conv_{variable.value}_{loop.value}.nc4.2022050514"
    diag_file = Path(current_app.config["DIAG_DIR"]) / filename

    # xarray.open_dataset doesn't distinguish between a file it can't understand
    # and a file that's not there. It raises a ValueError even for missing
    # files. We raise a FileNotFoundError to make debugging easier.
    if not diag_file.exists():
        raise FileNotFoundError(f"No such file: '{str(diag_file)}'")

    return xr.open_dataset(diag_file)


def wind(loop: MinimLoop) -> Optional[VectorDiag]:
    ds = open_diagnostic(Variable.WIND, loop)

    if not ds:
        return None

    observation = VectorVariable.from_vectors(ds["u_Observation"], ds["v_Observation"])
    forecast = VectorVariable.from_vectors(
        ds["u_Observation"] - ds["u_Obs_Minus_Forecast_unadjusted"],
        ds["v_Observation"] - ds["v_Obs_Minus_Forecast_unadjusted"],
    )

    data = VectorDiag(observation, forecast)

    return data
