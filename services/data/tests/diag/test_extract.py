import xarray as xr
from ugdata import diag


def test_load(diag_file, diag_dataset):
    """diag.load should return datasets for observations, forecasts, and results"""

    variable = "ps"
    loop = "anl"
    init_time = "2022050514"
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
