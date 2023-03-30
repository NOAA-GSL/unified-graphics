import os
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from typing import Generator, List, Union
from urllib.parse import urlparse

import numpy as np
import xarray as xr
import zarr  # type: ignore
from flask import current_app
from s3fs import S3FileSystem, S3Map  # type: ignore
from werkzeug.datastructures import MultiDict
from xarray.core.dataset import Dataset


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
Vector = namedtuple("Vector", "u v")


@dataclass
class Observation:
    variable: str
    variable_type: VariableType
    loop: MinimLoop
    adjusted: Union[float, Vector]
    unadjusted: Union[float, Vector]
    observed: Union[float, Vector]
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


ModelMetadata = namedtuple(
    "ModelMetadata",
    (
        "model_list system_list domain_list background_list frequency_list "
        "variable_list init_time_list"
    ),
)


def get_model_metadata() -> ModelMetadata:
    store = get_store(current_app.config["DIAG_ZARR"])
    z = zarr.open(store)

    model_list = set()
    system_list = set()
    domain_list = set()
    frequency_list = set()
    background_list = set()
    init_time_list = set()
    variable_list = set()

    for _, arr in z.arrays(True):
        model, system, domain, bg, freq, variable, init_time = arr.path.split("/")[:-2]
        model_list.add(model)
        system_list.add(system)
        domain_list.add(domain)
        frequency_list.add(freq)
        background_list.add(bg)
        variable_list.add(variable)
        init_time_list.add(init_time)

    return ModelMetadata(
        model_list,
        system_list,
        domain_list,
        background_list,
        frequency_list,
        variable_list,
        init_time_list,
    )


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
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    variable: Variable,
    initialization_time: str,
    loop: MinimLoop,
) -> xr.Dataset:
    store = get_store(current_app.config["DIAG_ZARR"])
    group = (
        f"/{model}/{system}/{domain}/{background}/{frequency}"
        f"/{variable.value}/{initialization_time}/{loop.value}"
    )
    return xr.open_zarr(store, group=group)


def parse_filter_value(value):
    if value == "true":
        return 1

    if value == "false":
        return 0

    try:
        return float(value)
    except ValueError:
        return value


# TODO: Refactor to a class
# I think this might belong in a different module. It could be a class or set of classes
# that represent different filters that can be added together into a filtering pipeline
def get_bounds(filters: MultiDict):
    for coord, value in filters.items():
        extent = np.array(
            [
                [parse_filter_value(digit) for digit in pair.split(",")]
                for pair in value.split("::")
            ]
        )
        yield coord, extent.min(axis=0), extent.max(axis=0)


def apply_filters(dataset: xr.Dataset, filters: MultiDict) -> Dataset:
    for coord, lower, upper in get_bounds(filters):
        data_array = dataset[coord]
        dataset = dataset.where((data_array >= lower) & (data_array <= upper)).dropna(
            dim="nobs"
        )

    # If the is_used filter is not passed, our default behavior is to include only used
    # observations.
    if "is_used" not in filters:
        dataset = dataset.where(dataset["is_used"]).dropna(dim="nobs")

    return dataset


def scalar(
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    variable: Variable,
    initialization_time: str,
    loop: MinimLoop,
    filters: MultiDict,
) -> List[Observation]:
    data = open_diagnostic(
        model,
        system,
        domain,
        background,
        frequency,
        variable,
        initialization_time,
        loop,
    )
    data = apply_filters(data, filters)

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
        for idx in range(data.dims["nobs"])
    ]


def temperature(
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    initialization_time: str,
    loop: MinimLoop,
    filters: MultiDict,
) -> List[Observation]:
    return scalar(
        model,
        system,
        domain,
        background,
        frequency,
        Variable.TEMPERATURE,
        initialization_time,
        loop,
        filters,
    )


def moisture(
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    initialization_time: str,
    loop: MinimLoop,
    filters: MultiDict,
) -> List[Observation]:
    return scalar(
        model,
        system,
        domain,
        background,
        frequency,
        Variable.MOISTURE,
        initialization_time,
        loop,
        filters,
    )


def pressure(
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    initialization_time: str,
    loop: MinimLoop,
    filters: MultiDict,
) -> List[Observation]:
    return scalar(
        model,
        system,
        domain,
        background,
        frequency,
        Variable.PRESSURE,
        initialization_time,
        loop,
        filters,
    )


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


def wind(
    model: str,
    system: str,
    domain: str,
    background: str,
    frequency: str,
    initialization_time: str,
    loop: MinimLoop,
    filters: MultiDict,
) -> List[Observation]:
    data = open_diagnostic(
        model,
        system,
        domain,
        background,
        frequency,
        Variable.WIND,
        initialization_time,
        loop,
    )
    data = apply_filters(data, filters)

    omf_adj_u = data["obs_minus_forecast_adjusted"].sel(component="u").values
    omf_adj_v = data["obs_minus_forecast_adjusted"].sel(component="v").values
    omf_una_u = data["obs_minus_forecast_unadjusted"].sel(component="u").values
    omf_una_v = data["obs_minus_forecast_unadjusted"].sel(component="v").values
    obs_u = data["observation"].sel(component="u").values
    obs_v = data["observation"].sel(component="v").values
    lng = data["longitude"].values
    lat = data["latitude"].values

    return [
        Observation(
            "wind",
            VariableType.VECTOR,
            loop,
            adjusted=Vector(
                round(float(omf_adj_u[idx]), 5), round(float(omf_adj_v[idx]), 5)
            ),
            unadjusted=Vector(
                round(float(omf_una_u[idx]), 5), round(float(omf_una_v[idx]), 5)
            ),
            observed=Vector(round(float(obs_u[idx]), 5), round(float(obs_v[idx]), 5)),
            position=Coordinate(round(float(lng[idx]), 5), round(float(lat[idx]), 5)),
        )
        for idx in range(data.dims["nobs"])
    ]


def magnitude(dataset: List[Observation]) -> Generator[Observation, None, None]:
    for obs in dataset:
        if isinstance(obs.adjusted, Vector):
            adjusted = vector_magnitude(obs.adjusted.u, obs.adjusted.v)
        else:
            adjusted = abs(obs.adjusted)

        if isinstance(obs.unadjusted, Vector):
            unadjusted = vector_magnitude(obs.unadjusted.u, obs.unadjusted.v)
        else:
            unadjusted = abs(obs.unadjusted)

        if isinstance(obs.observed, Vector):
            observed = vector_magnitude(obs.observed.u, obs.observed.v)
        else:
            observed = abs(obs.observed)

        yield Observation(
            obs.variable,
            obs.variable_type,
            obs.loop,
            adjusted=adjusted,
            unadjusted=unadjusted,
            observed=observed,
            position=obs.position,
        )
