from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Union

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
    PRESSURE = "ps"
    TEMPERATURE = "t"
    WIND = "uv"


class VariableType(Enum):
    SCALAR = "scalar"
    VECTOR = "vector"


Coordinate = namedtuple("Coordinate", "longitude latitude")
PolarCoordinate = namedtuple("PolarCoordinate", "magnitude direction")


@dataclass
class Observation:
    stationId: str
    variable: str
    variable_type: VariableType
    guess: Union[float, PolarCoordinate]
    analysis: Union[float, PolarCoordinate]
    observed: Union[float, PolarCoordinate]
    position: Coordinate

    def to_geojson(self):
        properties = {
            "stationId": self.stationId,
            "type": self.variable_type.value,
            "variable": self.variable,
        }

        if isinstance(self.guess, float):
            properties["guess"] = self.guess
            properties["analysis"] = self.analysis
            properties["observed"] = self.observed
        else:
            properties["guess"] = self.guess._asdict()
            properties["analysis"] = self.analysis._asdict()
            properties["observed"] = self.observed._asdict()

        return {
            "type": "Feature",
            "properties": properties,
            "geometry": {"type": "Point", "coordinates": list(self.position)},
        }


def open_diagnostic(variable: Variable, loop: MinimLoop) -> xr.Dataset:
    filename = f"ncdiag_conv_{variable.value}_{loop.value}.nc4.2022050514"
    diag_file = Path(current_app.config["DIAG_DIR"]) / filename

    # xarray.open_dataset doesn't distinguish between a file it can't understand
    # and a file that's not there. It raises a ValueError even for missing
    # files. We raise a FileNotFoundError to make debugging easier.
    if not diag_file.exists():
        raise FileNotFoundError(f"No such file: '{str(diag_file)}'")

    return xr.open_dataset(diag_file)


def scalar(variable: Variable) -> List[Observation]:
    ges = open_diagnostic(variable, MinimLoop.GUESS)
    anl = open_diagnostic(variable, MinimLoop.ANALYSIS)

    return [
        Observation(
            stationId.decode("utf-8").strip(),
            variable.name.lower(),
            VariableType.SCALAR,
            guess=float(ges["Obs_Minus_Forecast_adjusted"].values[idx]),
            analysis=float(anl["Obs_Minus_Forecast_adjusted"].values[idx]),
            observed=float(ges["Observation"].values[idx]),
            position=Coordinate(
                float(ges["Longitude"].values[idx] - 360),
                float(ges["Latitude"].values[idx]),
            ),
        )
        for idx, stationId in enumerate(ges["Station_ID"].values)
    ]


def temperature() -> List[Observation]:
    return scalar(Variable.TEMPERATURE)


def moisture() -> List[Observation]:
    return scalar(Variable.MOISTURE)


def pressure() -> List[Observation]:
    return scalar(Variable.PRESSURE)


def wind() -> List[Observation]:
    ges = open_diagnostic(Variable.WIND, MinimLoop.GUESS)
    anl = open_diagnostic(Variable.WIND, MinimLoop.ANALYSIS)

    # FIXME: This seems like this should be refactored into helper methods or
    # something. Although, ideally, I think all of these values should be
    # pre-calculated and stored on-disk as part of a pipeline that processes new
    # data.
    ges_mag = np.sqrt(
        ges["u_Obs_Minus_Forecast_adjusted"].values ** 2
        + ges["v_Obs_Minus_Forecast_adjusted"].values ** 2
    )
    ges_dir = (
        90
        - np.degrees(
            np.arctan2(
                -ges["v_Obs_Minus_Forecast_adjusted"].values,
                -ges["u_Obs_Minus_Forecast_adjusted"].values,
            )
        )
    ) % 360

    anl_mag = np.sqrt(
        anl["u_Obs_Minus_Forecast_adjusted"].values ** 2
        + anl["v_Obs_Minus_Forecast_adjusted"].values ** 2
    )
    anl_dir = (
        90
        - np.degrees(
            np.arctan2(
                -anl["v_Obs_Minus_Forecast_adjusted"].values,
                -anl["u_Obs_Minus_Forecast_adjusted"].values,
            )
        )
    ) % 360

    obs_mag = np.sqrt(
        ges["u_Observation"].values ** 2 + ges["v_Observation"].values ** 2
    )
    obs_dir = (
        90
        - np.degrees(
            np.arctan2(
                -ges["v_Observation"].values,
                -ges["u_Observation"].values,
            )
        )
    ) % 360

    return [
        Observation(
            stationId.decode("utf-8").strip(),
            "wind",
            VariableType.VECTOR,
            guess=PolarCoordinate(float(ges_mag[idx]), float(ges_dir[idx])),
            analysis=PolarCoordinate(float(anl_mag[idx]), float(anl_dir[idx])),
            observed=PolarCoordinate(float(obs_mag[idx]), float(obs_dir[idx])),
            position=Coordinate(
                float(ges["Longitude"].values[idx] - 360),
                float(ges["Latitude"].values[idx]),
            ),
        )
        for idx, stationId in enumerate(ges["Station_ID"].values)
    ]
