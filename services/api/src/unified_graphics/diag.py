from collections import namedtuple
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


class ValueType(Enum):
    OBSERVATION = "observation"
    FORECAST = "forecast"


class Variable(Enum):
    MOISTURE = "q"
    PRESSURE = "p"
    TEMPERATURE = "t"
    WIND = "uv"


Coordinate = namedtuple("Coordinate", "longitude latitude")
PolarCoordinate = namedtuple("PolarCoordinate", "magnitude direction")


@dataclass
class VectorObservation:
    stationId: str
    variable: str
    guess: PolarCoordinate
    analysis: PolarCoordinate
    observed: PolarCoordinate
    position: Coordinate

    def to_geojson(self):
        return {
            "type": "Feature",
            "properties": {
                "stationId": self.stationId,
                "variable": self.variable,
                "guess": self.guess._asdict(),
                "analysis": self.analysis._asdict(),
                "observed": self.observed._asdict(),
            },
            "geometry": {"type": "Point", "coordinates": list(self.position)},
        }


def temperature(loop: MinimLoop) -> List[float]:
    ds = open_diagnostic(Variable.TEMPERATURE, loop)
    return [float(v) for v in ds["Obs_Minus_Forecast_unadjusted"]]


def open_diagnostic(variable: Variable, loop: MinimLoop) -> xr.Dataset:
    filename = f"ncdiag_conv_{variable.value}_{loop.value}.nc4.2022050514"
    diag_file = Path(current_app.config["DIAG_DIR"]) / filename

    # xarray.open_dataset doesn't distinguish between a file it can't understand
    # and a file that's not there. It raises a ValueError even for missing
    # files. We raise a FileNotFoundError to make debugging easier.
    if not diag_file.exists():
        raise FileNotFoundError(f"No such file: '{str(diag_file)}'")

    return xr.open_dataset(diag_file)


def wind() -> List[VectorObservation]:
    ges = open_diagnostic(Variable.WIND, MinimLoop.GUESS)
    anl = open_diagnostic(Variable.WIND, MinimLoop.ANALYSIS)

    # FIXME: This seems like this should be refactored into helper methods or
    # something. Although, ideally, I think all of these values should be
    # pre-calculated and stored on-disk as part of a pipeline that processes new
    # data.
    ges_mag = np.sqrt(
        ges["u_Obs_Minus_Forecast_adjusted"] ** 2
        + ges["v_Obs_Minus_Forecast_adjusted"] ** 2
    )
    ges_dir = (
        90
        - np.degrees(
            np.arctan2(
                -ges["v_Obs_Minus_Forecast_adjusted"],
                -ges["u_Obs_Minus_Forecast_adjusted"],
            )
        )
    ) % 360

    anl_mag = np.sqrt(
        anl["u_Obs_Minus_Forecast_adjusted"] ** 2
        + anl["v_Obs_Minus_Forecast_adjusted"] ** 2
    )
    anl_dir = (
        90
        - np.degrees(
            np.arctan2(
                -anl["v_Obs_Minus_Forecast_adjusted"],
                -anl["u_Obs_Minus_Forecast_adjusted"],
            )
        )
    ) % 360

    obs_mag = np.sqrt(ges["u_Observation"] ** 2 + ges["v_Observation"] ** 2)
    obs_dir = (
        90
        - np.degrees(
            np.arctan2(
                -ges["v_Observation"],
                -ges["u_Observation"],
            )
        )
    ) % 360

    return [
        VectorObservation(
            stationId.decode("utf-8").strip(),
            "wind",
            guess=PolarCoordinate(
                float(ges_mag.values[idx]), float(ges_dir.values[idx])
            ),
            analysis=PolarCoordinate(
                float(anl_mag.values[idx]), float(anl_dir.values[idx])
            ),
            observed=PolarCoordinate(
                float(obs_mag.values[idx]), float(obs_dir.values[idx])
            ),
            position=Coordinate(
                float(ges["Longitude"].values[idx]), float(ges["Latitude"].values[idx])
            ),
        )
        for idx, stationId in enumerate(ges["Station_ID"].values)
    ]
