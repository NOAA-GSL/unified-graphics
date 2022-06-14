from enum import Enum
from typing import Dict
import os

from flask import current_app
import numpy as np
import xarray as xr


class MinimLoop(Enum):
    GUESS = "ges"
    ANALYSIS = "anl"


def get_filepath(loop) -> str:
    return os.path.join(
        current_app.config["DIAG_DIR"], f"ncdiag_conv_t_{loop.value}.nc4.20220514"
    )


def get_diagnostics() -> Dict:
    ds = xr.open_dataset("data/ncdiag_conv_t_ges.nc4.20220514")
    obs_minus_fcast = ds["Obs_Minus_Forecast_adjusted"].values

    obs_count = len(obs_minus_fcast)
    mean = np.mean(obs_minus_fcast)
    std = np.std(obs_minus_fcast)
    counts, bins = np.histogram(obs_minus_fcast, bins="auto")

    distribution = [
        {"lower": bins[idx], "upper": bins[idx + 1], "value": int(count)}
        for idx, count in enumerate(counts)
    ]

    return {
        "bins": distribution,
        "observations": obs_count,
        "std": std,
        "mean": mean,
    }
