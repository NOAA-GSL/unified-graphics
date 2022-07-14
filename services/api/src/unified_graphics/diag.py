from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List

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
        direction = (90 - np.degrees(np.arctan2(-v, -u))) % 360
        magnitude = np.sqrt(u**2 + v**2)

        # Set the direction on any (0, 0) vectors to 0, so we don’t have to deal
        # with this 0.0 vs -0.0 silliness from np.arctan2 and to be consistent
        # with the NCL wind_direction function we used as a reference.
        calm = magnitude == 0
        direction[calm] = 0

        return cls(
            direction=[float(d) for d in direction],
            magnitude=[float(m) for m in magnitude],
        )


@dataclass
class Bin:
    lower: float
    upper: float
    value: float


@dataclass
class ScalarDiag:
    bins: List[Bin]
    observations: int
    std: float
    mean: float

    @classmethod
    def from_array(cls, data: xr.DataArray) -> "ScalarDiag":
        return cls(bins=[], observations=0, std=0.0, mean=0.0)


@dataclass
class VectorDiag:
    observation: VectorVariable
    forecast: VectorVariable


def temperature(loop: MinimLoop) -> ScalarDiag:
    ds = open_diagnostic(Variable.TEMPERATURE, loop)
    return ScalarDiag.from_array(ds["Obs_Minus_Forecast_adjusted"])


def open_diagnostic(variable: Variable, loop: MinimLoop) -> xr.Dataset:
    filename = f"ncdiag_conv_{variable.value}_{loop.value}.nc4.2022050514"
    diag_file = Path(current_app.config["DIAG_DIR"]) / filename

    # xarray.open_dataset doesn't distinguish between a file it can't understand
    # and a file that's not there. It raises a ValueError even for missing
    # files. We raise a FileNotFoundError to make debugging easier.
    if not diag_file.exists():
        raise FileNotFoundError(f"No such file: '{str(diag_file)}'")

    return xr.open_dataset(diag_file)


def wind(loop: MinimLoop) -> VectorDiag:
    ds = open_diagnostic(Variable.WIND, loop)

    observation = VectorVariable.from_vectors(ds["u_Observation"], ds["v_Observation"])
    forecast = VectorVariable.from_vectors(
        ds["u_Observation"] - ds["u_Obs_Minus_Forecast_unadjusted"],
        ds["v_Observation"] - ds["v_Obs_Minus_Forecast_unadjusted"],
    )

    data = VectorDiag(observation, forecast)

    return data
