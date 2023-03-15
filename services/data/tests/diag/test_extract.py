import numpy as np
import pytest
import xarray as xr
from ugdata import diag


@pytest.mark.parametrize(
    "filename,variables,loop,init_time,background",
    [
        ("diag_ps_anl.202205051400.nc4", ["ps"], "anl", "2022-05-05T14:00", None),
        ("diag_ps_02.202205051400.nc4", ["ps"], "02", "2022-05-05T14:00", None),
        ("diag_uv_ges.202301020400.nc4", ["u", "v"], "ges", "2023-01-02T04:00", None),
        (
            "diag_ps_anl.202205051400.HRRR.nc4",
            ["ps"],
            "anl",
            "2022-05-05T14:00",
            "HRRR",
        ),
        ("ncdiag_conv_ps_anl.2022050514.nc4", ["ps"], "anl", "2022-05-05T14", None),
        ("ncdiag_conv_uv_ges.2023010204.nc4", ["u", "v"], "ges", "2023-01-02T04", None),
        (
            (
                "2a563509-3785-486a-b0d4-2810e3820abf-UDD_3DRTMA_HRRR_DIAG_"
                "diag_uv_ges.202302011400.nc4"
            ),
            ["u", "v"],
            "ges",
            "2023-02-01T14:00",
            None,
        ),
    ],
)
def test_parse_diag_filename(filename, variables, loop, init_time, background):
    """diag.parse_diag_filename should return the variable, loop, and
    initialization time from a diag filename
    """
    result = diag.parse_diag_filename(filename)
    assert result == (variables, loop, init_time, background)


@pytest.mark.parametrize(
    "filename,errmsg",
    [
        ("ncdiag_s_anl.2022050514.nc4", "Invalid diagnostics filename"),
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
    "variable,loop,init_time,background,coords",
    [
        ("ps", "anl", "2022050514", None, {}),
        ("q", "anl", "2022050514", "HRRR", {}),
        ("t", "anl", "2022050514", "HRRR", {}),
    ],
)
def test_load(variable, loop, init_time, background, coords, diag_file, diag_dataset):
    """diag.load should return datasets for observations, forecasts, and results"""

    test_file = diag_file(variable, loop, init_time, background)
    expected_init_time = (
        f"{init_time[:4]}-{init_time[4:6]}-{init_time[6:8]}T{init_time[-2:]}"
    )
    expected = diag_dataset(variable, expected_init_time, loop, background, **coords)

    result = diag.load(test_file)

    xr.testing.assert_equal(result, expected)
    assert result.attrs == expected.attrs
