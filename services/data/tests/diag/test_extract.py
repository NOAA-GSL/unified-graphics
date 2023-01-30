import pytest
import xarray as xr
from ugdata import diag


@pytest.mark.parametrize(
    "variable,loop,init_time",
    [
        ("ps", "anl", "2022050514"),
        ("q", "anl", "2022050514"),
        ("t", "anl", "2022050514"),
        ("uv", "anl", "2022050514"),
    ],
)
def test_load(variable, loop, init_time, diag_file, diag_dataset):
    """diag.load should return datasets for observations, forecasts, and results"""

    test_file = diag_file(variable, loop, init_time)

    result = diag.load(test_file)

    assert result
    result_observations, result_forecast, result_difference = result
    xr.testing.assert_equal(
        result_difference,
        diag_dataset("difference", [variable], init_time, loop, is_adjusted=[0, 1]),
    )
    xr.testing.assert_equal(
        result_forecast,
        diag_dataset("forecast", [variable], init_time, loop, is_adjusted=[0, 1]),
    )
    xr.testing.assert_equal(
        result_observations, diag_dataset("observations", [variable], init_time, loop)
    )
