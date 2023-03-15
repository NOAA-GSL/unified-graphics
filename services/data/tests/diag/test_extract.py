import numpy as np
import pytest
import xarray as xr
from ugdata import diag


@pytest.mark.parametrize(
    "filename,variables,loop,init_time,prefix,model,system,domain,frequency,background",
    [
        (
            "diag_ps_anl.202205051400.nc4",
            ["ps"],
            "anl",
            "2022-05-05T14:00",
            None,
            None,
            None,
            None,
            None,
            None,
        ),
        (
            "diag_ps_02.202205051400.nc4",
            ["ps"],
            "02",
            "2022-05-05T14:00",
            None,
            None,
            None,
            None,
            None,
            None,
        ),
        (
            "/RTMA/WCOSS/CONUS/RETRO/diag_uv_ges.202301020400.nc4",
            ["u", "v"],
            "ges",
            "2023-01-02T04:00",
            "/",
            "RTMA",
            "WCOSS",
            "CONUS",
            "RETRO",
            None,
        ),
        (
            "/prefix/RTMA/WCOSS/CONUS/REALTIME/diag_ps_anl.202205051400.HRRR.nc4",
            ["ps"],
            "anl",
            "2022-05-05T14:00",
            "/prefix",
            "RTMA",
            "WCOSS",
            "CONUS",
            "REALTIME",
            "HRRR",
        ),
        (
            # In this test the model is missing from the path; after the prefix we have
            # the system, domain, and frequency. It is expected behavior that everything
            # is shifted because we don't do any validation of these values, they are
            # interpreted based on position. Therefore, WCOSS is interpreted as the
            # model, and the frequency ends up as None, despite the fact that it's
            # actually the model that's missing.
            "/prefix/WCOSS/CONUS/REALTIME/diag_ps_anl.202205051400.HRRR.nc4",
            ["ps"],
            "anl",
            "2022-05-05T14:00",
            "/prefix",
            "WCOSS",
            "CONUS",
            "REALTIME",
            None,
            "HRRR",
        ),
        (
            "ncdiag_conv_ps_anl.2022050514.nc4",
            ["ps"],
            "anl",
            "2022-05-05T14",
            None,
            None,
            None,
            None,
            None,
            None,
        ),
        (
            "ncdiag_conv_uv_ges.2023010204.nc4",
            ["u", "v"],
            "ges",
            "2023-01-02T04",
            None,
            None,
            None,
            None,
            None,
            None,
        ),
        (
            (
                "2a563509-3785-486a-b0d4-2810e3820abf-UDD_3DRTMA_HRRR_DIAG_"
                "diag_uv_ges.202302011400.nc4"
            ),
            ["u", "v"],
            "ges",
            "2023-02-01T14:00",
            None,
            None,
            None,
            None,
            None,
            None,
        ),
    ],
)
def test_parse_diag_filename(
    filename,
    variables,
    loop,
    init_time,
    prefix,
    model,
    system,
    domain,
    frequency,
    background,
):
    """diag.parse_diag_filename should return the variable, loop, and
    initialization time from a diag filename
    """
    result = diag.parse_diag_filename(filename, prefix=prefix)
    assert result == (
        variables,
        loop,
        init_time,
        model,
        system,
        domain,
        frequency,
        background,
    )


@pytest.mark.parametrize(
    "filename,prefix,errmsg",
    [
        ("ncdiag_s_anl.2022050514.nc4", None, "Invalid diagnostics filename"),
        ("ncdiag_conv_ps_anl.nc4.20220505", None, "Invalid diagnostics filename"),
        (
            "diag_ps_anl.202205051400.nc4",
            "/prefix",
            "'diag_ps_anl.202205051400.nc4' is not in the subpath of '/prefix'",
        ),
        (
            "/different/prefix/diag_ps_anl.202205051400.nc4",
            "/prefix",
            (
                "'/different/prefix/diag_ps_anl.202205051400.nc4' "
                "is not in the subpath of '/prefix'"
            ),
        ),
    ],
)
def test_parse_diag_filename_invalid(filename, prefix, errmsg):
    """diag.parse_diag_filename should raise a ValueError if the filename can't
    be parsed
    """
    with pytest.raises(ValueError) as excinfo:
        diag.parse_diag_filename(filename, prefix)

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
    "variable,loop,init_time,model,system,domain,frequency,background,coords",
    [
        ("ps", "anl", "2022050514", None, None, None, None, None, {}),
        ("q", "anl", "2022050514", "RTMA", "WCOSS", "CONUS", "REALTIME", "HRRR", {}),
        ("t", "anl", "2022050514", "RTMA", "WCOSS", "CONUS", "REALTIME", "HRRR", {}),
    ],
)
def test_load(
    variable,
    loop,
    init_time,
    model,
    system,
    domain,
    frequency,
    background,
    coords,
    diag_file,
    diag_dataset,
    tmp_path,
):
    """diag.load should return datasets for observations, forecasts, and results"""

    test_file = diag_file(
        variable, loop, init_time, model, system, domain, frequency, background
    )
    expected_init_time = (
        f"{init_time[:4]}-{init_time[4:6]}-{init_time[6:8]}T{init_time[-2:]}"
    )
    expected = diag_dataset(
        variable,
        expected_init_time,
        loop,
        model,
        system,
        domain,
        frequency,
        background,
        **coords,
    )

    result = diag.load(test_file, prefix=str(tmp_path))

    xr.testing.assert_equal(result, expected)
    assert result.attrs == expected.attrs
