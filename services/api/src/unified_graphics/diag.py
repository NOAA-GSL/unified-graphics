import os
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Union
from urllib.parse import urlparse

import fsspec  # type: ignore
import numpy as np
import xarray as xr
from flask import current_app
from s3fs import S3FileSystem, S3Map


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
    guess: Union[float, PolarCoordinate]
    analysis: Union[float, PolarCoordinate]
    observed: Union[float, PolarCoordinate]
    position: Coordinate

    def to_geojson(self):
        properties = {
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


def scalar(variable: Variable, initialization_time: str) -> List[Observation]:
    ges = open_diagnostic(variable, initialization_time, MinimLoop.GUESS)
    anl = open_diagnostic(variable, initialization_time, MinimLoop.ANALYSIS)

    return [
        Observation(
            variable.name.lower(),
            VariableType.SCALAR,
            guess=float(ges["obs_minus_forecast_adjusted"].values[idx]),
            analysis=float(anl["obs_minus_forecast_adjusted"].values[idx]),
            observed=float(ges["observation"].values[idx]),
            position=Coordinate(
                float(ges["longitude"].values[idx]),
                float(ges["latitude"].values[idx]),
            ),
        )
        for idx in range(len(ges["observation"]))
    ]


def temperature(initialization_time) -> List[Observation]:
    return scalar(Variable.TEMPERATURE, initialization_time)


def moisture(initialization_time) -> List[Observation]:
    return scalar(Variable.MOISTURE, initialization_time)


def pressure(initialization_time) -> List[Observation]:
    return scalar(Variable.PRESSURE, initialization_time)


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


def wind(initialization_time: str) -> List[Observation]:
    ges = open_diagnostic(Variable.WIND, initialization_time, MinimLoop.GUESS)
    anl = open_diagnostic(Variable.WIND, initialization_time, MinimLoop.ANALYSIS)

    ges_forecast_u = ges["observation"].sel(component="u") - ges[
        "obs_minus_forecast_adjusted"
    ].sel(component="u")
    ges_forecast_v = ges["observation"].sel(component="v") - ges[
        "obs_minus_forecast_adjusted"
    ].sel(component="v")

    anl_forecast_u = anl["observation"].sel(component="u") - anl[
        "obs_minus_forecast_adjusted"
    ].sel(component="u")
    anl_forecast_v = anl["observation"].sel(component="v") - anl[
        "obs_minus_forecast_adjusted"
    ].sel(component="v")

    ges_forecast_mag = vector_magnitude(ges_forecast_u.values, ges_forecast_v.values)
    ges_forecast_dir = vector_direction(ges_forecast_u.values, ges_forecast_v.values)

    anl_forecast_mag = vector_magnitude(anl_forecast_u.values, anl_forecast_v.values)
    anl_forecast_dir = vector_direction(anl_forecast_u.values, anl_forecast_v.values)

    obs_mag = vector_magnitude(
        ges["observation"].sel(component="u").values,
        ges["observation"].sel(component="v").values,
    )
    obs_dir = vector_direction(
        ges["observation"].sel(component="u").values,
        ges["observation"].sel(component="v").values,
    )

    ges_mag = obs_mag - ges_forecast_mag
    ges_dir = obs_dir - ges_forecast_dir

    anl_mag = obs_mag - anl_forecast_mag
    anl_dir = obs_dir - anl_forecast_dir

    return [
        Observation(
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
                round(float(ges["longitude"].values[idx]), 5),
                round(float(ges["latitude"].values[idx]), 5),
            ),
        )
        for idx in range(len(ges["observation"].values))
    ]
