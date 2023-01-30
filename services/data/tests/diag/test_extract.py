import pytest
import xarray as xr
from ugdata import diag


@pytest.mark.parametrize(
    "filename,variables,loop,init_time",
    [
        ("ncdiag_conv_ps_anl.nc4.2022050514", ["ps"], "anl", "2022-05-05T14"),
        ("ncdiag_conv_uv_ges.nc4.2023010204", ["u", "v"], "ges", "2023-01-02T04"),
    ],
)
def test_parse_diag_filename(filename, variables, loop, init_time):
    """diag.parse_diag_filename should return the variable, loop, and
    initialization time from a diag filename
    """
    result = diag.parse_diag_filename(filename)
    assert result == (variables, loop, init_time)


@pytest.mark.parametrize(
    "filename,errmsg",
    [
        ("ncdiag_ps_anl.nc4.2022050514", "Invalid diagnostics filename"),
        ("ncdiag_conv_ps_anl.nc4.202205051400", "Unrecognized date format in filename"),
    ],
)
def test_parse_diag_filename_invalid(filename, errmsg):
    """diag.parse_diag_filename should raise a ValueError if the filename can't
    be parsed
    """
    with pytest.raises(ValueError) as excinfo:
        diag.parse_diag_filename(filename)

    assert errmsg in str(excinfo.value)


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
