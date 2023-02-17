import os
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from typing import Iterator, List, Union
from urllib.parse import urlparse

import numpy as np
import xarray as xr
import zarr  # type: ignore
from flask import current_app
from s3fs import S3FileSystem, S3Map  # type: ignore


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
    variable: str
    variable_type: VariableType
    loop: MinimLoop
    adjusted: Union[float, PolarCoordinate]
    unadjusted: Union[float, PolarCoordinate]
    observed: Union[float, PolarCoordinate]
    position: Coordinate

    def to_geojson(self):
        properties = {
            "type": self.variable_type.value,
            "variable": self.variable,
            "loop": self.loop.value,
        }

        if isinstance(self.adjusted, float):
            properties["adjusted"] = self.adjusted
            properties["unadjusted"] = self.unadjusted
            properties["observed"] = self.observed
        else:
            properties["adjusted"] = self.adjusted._asdict()
            properties["unadjusted"] = self.unadjusted._asdict()
            properties["observed"] = self.observed._asdict()

        return {
            "type": "Feature",
            "properties": properties,
            "geometry": {"type": "Point", "coordinates": list(self.position)},
        }


def initialization_times(variable: str) -> Iterator[str]:
    store = get_store(current_app.config["DIAG_ZARR"])
    z = zarr.open(store)

    v = getattr(Variable, variable.upper())

    if v.value not in z:
        raise FileNotFoundError(f"Variable '{v.value}' not found in diagnostic file")

    return z[v.value].group_keys()


def loops(variable: str, initialization_time: str) -> Iterator[str]:
    store = get_store(current_app.config["DIAG_ZARR"])
    z = zarr.open(store)
    v = getattr(Variable, variable.upper())

    if v.value not in z:
        raise FileNotFoundError(f"Variable '{v.value}' not found in diagnostic file")

    if initialization_time not in z[v.value]:
        raise FileNotFoundError(
            f"Initialization time '{initialization_time}' not found in diagnostic file"
        )

    return z[v.value][initialization_time].group_keys()


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
    variable: Variable, initialization_time: str, loop: MinimLoop
) -> xr.Dataset:
    store = get_store(current_app.config["DIAG_ZARR"])
    group = f"/{variable.value}/{initialization_time}/{loop.value}"
    return xr.open_zarr(store, group=group)


def scalar(
    variable: Variable, initialization_time: str, loop: MinimLoop
) -> List[Observation]:
    data = open_diagnostic(variable, initialization_time, loop)

    return [
        Observation(
            variable.name.lower(),
            VariableType.SCALAR,
            loop,
            adjusted=float(data["obs_minus_forecast_adjusted"].values[idx]),
            unadjusted=float(data["obs_minus_forecast_unadjusted"].values[idx]),
            observed=float(data["observation"].values[idx]),
            position=Coordinate(
                float(data["longitude"].values[idx]),
                float(data["latitude"].values[idx]),
            ),
        )
        for idx in range(len(data["observation"]))
    ]


def temperature(initialization_time: str, loop: MinimLoop) -> List[Observation]:
    return scalar(Variable.TEMPERATURE, initialization_time, loop)


def moisture(initialization_time: str, loop: MinimLoop) -> List[Observation]:
    return scalar(Variable.MOISTURE, initialization_time, loop)


def pressure(initialization_time: str, loop: MinimLoop) -> List[Observation]:
    return scalar(Variable.PRESSURE, initialization_time, loop)


def vector_direction(u, v):
    direction = (90 - np.degrees(np.arctan2(-v, -u))) % 360

    # Anywhere the magnitude of the vector is 0
    calm = (np.abs(u) == 0) & (np.abs(v) == 0)

    # numpy.arctan2 treats 0.0 and -0.0 differently. Whenever the second
    # argument to the function is -0.0, it return pi or -pi depending on the
    # sign of the first argument. Whenever the second argument is 0.0, it will
    # return 0.0 or -0.0 depending on the sign of the first argument. We
    # normalize all calm vectors (magnitude 0) to have a direction of 0.0, per
    # the NCAR Command Language docs.
    # http://ncl.ucar.edu/Document/Functions/Contributed/wind_direction.shtml
    direction[calm] = 0.0

    return direction


def vector_magnitude(u, v):
    return np.sqrt(u**2 + v**2)


def wind(initialization_time: str, loop: MinimLoop) -> List[Observation]:
    data = open_diagnostic(Variable.WIND, initialization_time, loop)

    forecast_u_adjusted = data["observation"].sel(component="u") - data[
        "obs_minus_forecast_adjusted"
    ].sel(component="u")
    forecast_v_adjusted = data["observation"].sel(component="v") - data[
        "obs_minus_forecast_adjusted"
    ].sel(component="v")

    forecast_u_unadjusted = data["observation"].sel(component="u") - data[
        "obs_minus_forecast_unadjusted"
    ].sel(component="u")
    forecast_v_unadjusted = data["observation"].sel(component="v") - data[
        "obs_minus_forecast_unadjusted"
    ].sel(component="v")

    adjusted_mag = vector_magnitude(
        forecast_u_adjusted.values, forecast_v_adjusted.values
    )
    adjusted_dir = vector_direction(
        forecast_u_adjusted.values, forecast_v_adjusted.values
    )

    unadjusted_mag = vector_magnitude(
        forecast_u_unadjusted.values, forecast_v_unadjusted.values
    )
    unadjusted_dir = vector_direction(
        forecast_u_unadjusted.values, forecast_v_unadjusted.values
    )

    obs_mag = vector_magnitude(
        data["observation"].sel(component="u").values,
        data["observation"].sel(component="v").values,
    )
    obs_dir = vector_direction(
        data["observation"].sel(component="u").values,
        data["observation"].sel(component="v").values,
    )

    adjusted_mag = obs_mag - adjusted_mag
    adjusted_dir = obs_dir - adjusted_dir

    unadjusted_mag = obs_mag - unadjusted_mag
    unadjusted_dir = obs_dir - unadjusted_dir

    return [
        Observation(
            "wind",
            VariableType.VECTOR,
            loop,
            adjusted=PolarCoordinate(
                round(float(adjusted_mag[idx]), 5), round(float(adjusted_dir[idx]), 5)
            ),
            unadjusted=PolarCoordinate(
                round(float(unadjusted_mag[idx]), 5),
                round(float(unadjusted_dir[idx]), 5),
            ),
            observed=PolarCoordinate(
                round(float(obs_mag[idx]), 5), round(float(obs_dir[idx]), 5)
            ),
            position=Coordinate(
                round(float(data["longitude"].values[idx]), 5),
                round(float(data["latitude"].values[idx]), 5),
            ),
        )
        for idx in range(len(data["observation"].values))
    ]
