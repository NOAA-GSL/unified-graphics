from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Union

import fsspec  # type: ignore
import xarray as xr
from flask import current_app

from . import vector


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
    diag_uri = current_app.config["DIAG_DIR"]

    if diag_uri.startswith("file://"):
        return open_local_diagnostic(diag_uri, filename)
    elif diag_uri.startswith("s3://"):
        return open_s3_diagnostic(diag_uri, filename)
    else:
        raise FileNotFoundError(f"Unknown file URI: '{str(diag_uri)}'")


def open_local_diagnostic(diag_uri: str, filename: str) -> xr.Dataset:
    """Opens a local diag file"""
    diag_uri = diag_uri.removeprefix("file://")  # Path doesn't support file URIs
    diag_file = Path(diag_uri) / filename

    # xarray.open_dataset doesn't distinguish between a file it can't understand
    # and a file that's not there. It raises a ValueError even for missing
    # files. We raise a FileNotFoundError to make debugging easier.
    if not diag_file.exists():
        current_app.logger.error(f"No such file: '{str(diag_file)}'")
        raise FileNotFoundError(f"No such file: '{str(diag_file)}'")

    return xr.open_dataset(diag_file)


# TODO - logger statements don't appear to be printing - at least in pytests
def open_s3_diagnostic(diag_uri: str, filename: str) -> xr.Dataset:
    """Opens a diag file stored in S3

    Assumes AWS S3, and grabs credentials via Boto3 defaults.

    If FLASK_ENDPOINT_URL is set in the environment, it will attempt to access
    an S3-like server at the URL provided. This is mostly useful for testing.
    """
    try:
        endpoint_url = current_app.config["ENDPOINT_URL"]
    except KeyError:
        endpoint_url = None
    cache = current_app.config["LOCAL_CACHE_PATH"]
    current_app.logger.info(f"Endpoint url set to: {endpoint_url}")
    diag_file = diag_uri + filename  # Path doesn't support file URIs

    # xarray.open_dataset can't open netcdf datasets natively - only
    # Zarr datasets. We'll use fsspec to cache the file locally so xarray
    # can access it from disk.
    try:
        # TODO - if statement is a workaround
        # TODO - for: https://github.com/fsspec/s3fs/issues/400
        if endpoint_url:
            with fsspec.open(
                f"simplecache::{diag_file}",
                s3={"anon": False, "client_kwargs": {"endpoint_url": endpoint_url}},
                simplecache={"cache_storage": cache},
            ) as f:
                ds_contents = xr.open_dataset(f.name)
        else:
            with fsspec.open(
                f"simplecache::{diag_file}",
                s3={"anon": False},
                simplecache={"cache_storage": cache},
            ) as f:
                ds_contents = xr.open_dataset(f.name)
    except FileNotFoundError as e:
        current_app.logger.error(
            f"The following bucket or key don't exist: '{str(diag_file)}'",
            exc_info=True,
        )
        raise e
    except PermissionError as e:
        current_app.logger.error(
            f"Permissions issue accessing: '{str(diag_file)}'", exc_info=True
        )
        raise e
    except ValueError as e:
        current_app.logger.error(
            f"Unknown file type: '{str(diag_file)}'", exc_info=True
        )
        raise e
    return ds_contents


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

    ges_forecast_u = ges["u_Observation"] - ges["u_Obs_Minus_Forecast_adjusted"]
    ges_forecast_v = ges["v_Observation"] - ges["v_Obs_Minus_Forecast_adjusted"]

    anl_forecast_u = anl["u_Observation"] - anl["u_Obs_Minus_Forecast_adjusted"]
    anl_forecast_v = anl["v_Observation"] - anl["v_Obs_Minus_Forecast_adjusted"]

    ges_forecast_mag = vector.magnitude(ges_forecast_u.values, ges_forecast_v.values)
    ges_forecast_dir = vector.direction(ges_forecast_u.values, ges_forecast_v.values)

    anl_forecast_mag = vector.magnitude(anl_forecast_u.values, anl_forecast_v.values)
    anl_forecast_dir = vector.direction(anl_forecast_u.values, anl_forecast_v.values)

    obs_mag = vector.magnitude(ges["u_Observation"].values, ges["v_Observation"].values)
    obs_dir = vector.direction(ges["u_Observation"].values, ges["v_Observation"].values)

    ges_mag = obs_mag - ges_forecast_mag
    ges_dir = obs_dir - ges_forecast_dir

    anl_mag = obs_mag - anl_forecast_mag
    anl_dir = obs_dir - anl_forecast_dir

    return [
        Observation(
            stationId.decode("utf-8").strip(),
            "wind",
            VariableType.VECTOR,
            guess=PolarCoordinate(
                round(float(ges_mag[idx]), 5), round(float(ges_dir[idx]), 5)
            ),
            analysis=PolarCoordinate(
                round(float(anl_mag[idx]), 5), round(float(anl_dir[idx]), 5)
            ),
            observed=PolarCoordinate(
                round(float(obs_mag[idx]), 5), round(float(obs_dir[idx]), 5)
            ),
            position=Coordinate(
                round(float(ges["Longitude"].values[idx] - 360), 5),
                round(float(ges["Latitude"].values[idx]), 5),
            ),
        )
        for idx, stationId in enumerate(ges["Station_ID"].values)
    ]
