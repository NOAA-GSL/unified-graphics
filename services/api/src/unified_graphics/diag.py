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


@dataclass
class VectorVariable:
    direction: List[float]
    magnitude: List[float]
    coords: List[Coordinate]

    @classmethod
    def from_vectors(
        cls, u: xr.DataArray, v: xr.DataArray, lng: xr.DataArray, lat: xr.DataArray
    ) -> "VectorVariable":

        # Ensure that all data arrays are the same length
        assert all(u.shape == a.shape for a in [v, lng, lat])

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
            coords=coordinate_pairs_from_vectors(lng, lat),
        )


def coordinate_pairs_from_vectors(
    lng: xr.DataArray, lat: xr.DataArray
) -> List[Coordinate]:
    assert lng.shape == lat.shape

    return [Coordinate(longitude=float(x), latitude=float(y)) for x, y in zip(lng, lat)]


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
    return [VectorObservation("WV270", "wind", (1, 180), (0.5, 0), (1, 90), (0, 0))]
