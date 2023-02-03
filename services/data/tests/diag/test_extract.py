import numpy as np
import pytest
import xarray as xr
from ugdata import diag


@pytest.mark.parametrize(
    "filename,variables,loop,init_time",
    [
        ("diag_ps_anl.202205051400.nc4", ["ps"], "anl", "2022-05-05T14:00"),
        ("diag_ps_02.202205051400.nc4", ["ps"], "02", "2022-05-05T14:00"),
        ("diag_uv_ges.202301020400.nc4", ["u", "v"], "ges", "2023-01-02T04:00"),
        ("ncdiag_conv_ps_anl.nc4.2022050514", ["ps"], "anl", "2022-05-05T14"),
        ("ncdiag_conv_uv_ges.nc4.2023010204", ["u", "v"], "ges", "2023-01-02T04"),
        (
            (
                "2a563509-3785-486a-b0d4-2810e3820abf-UDD_3DRTMA_HRRR_DIAG_"
                "diag_uv_ges.202302011400.nc4"
            ),
            ["u", "v"],
            "ges",
            "2023-02-01T14:00",
        ),
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
        ("ncdiag_s_anl.2022050514.nc4", "Invalid diagnostics filename"),
        ("diag_ps_02.202205051400.nc4", "Invalid diagnostics filename"),
        ("ncdiag_conv_ps_anl.nc4.20220505", "Invalid diagnostics filename"),
    ],
)
def test_parse_diag_filename_invalid(filename, errmsg):
    """diag.parse_diag_filename should raise a ValueError if the filename can't
    be parsed
    """
    with pytest.raises(ValueError) as excinfo:
        diag.parse_diag_filename(filename)

    assert errmsg in str(excinfo.value)


@pytest.mark.parametrize("variable", ["Observation", "Forecast_adjusted"])
def test_get_data_array_scalar(variable):
    ds = xr.Dataset(
        {
            "Observation": (["nobs"], np.zeros((1,))),
            "Forecast_adjusted": (["nobs"], np.zeros((1,))),
        }
    )

    result = diag.get_data_array(ds, variable)

    xr.testing.assert_equal(result, ds[variable])


@pytest.mark.parametrize("variable", ["Observation", "Forecast_adjusted"])
def test_get_data_array_vector(variable):
    ds = xr.Dataset(
        {
            "u_Observation": (["nobs"], np.zeros((1,))),
            "v_Observation": (["nobs"], np.zeros((1,))),
            "u_Forecast_adjusted": (["nobs"], np.zeros((1,))),
            "v_Forecast_adjusted": (["nobs"], np.zeros((1,))),
        }
    )

    result = diag.get_data_array(ds, variable, components=["u", "v"])

    exp = xr.DataArray(
        np.zeros((1, 2)),
        coords={"component": ["u", "v"]},
        dims=["nobs", "component"],
        attrs={"name": variable},
    )

    xr.testing.assert_equal(result, exp)


@pytest.mark.parametrize(
    "variable,loop,init_time,coords",
    [
        ("ps", "anl", "2022050514", {}),
        ("q", "anl", "2022050514", {}),
        ("t", "anl", "2022050514", {}),
    ],
)
def test_load(variable, loop, init_time, coords, diag_file, diag_dataset):
    """diag.load should return datasets for observations, forecasts, and results"""

    test_file = diag_file(variable, loop, init_time)

    result = diag.load(test_file)

    xr.testing.assert_equal(
        result,
        diag_dataset(variable, init_time, loop, **coords),
    )
