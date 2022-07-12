from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import os

from flask import current_app
import numpy as np
import xarray as xr


class MinimLoop(Enum):
    GUESS = "ges"
    ANALYSIS = "anl"


@dataclass
class VectorVariable:
    direction: List[float]
    magnitude: List[float]


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


def wind(loop: MinimLoop) -> Optional[VectorDiag]:
    return None
