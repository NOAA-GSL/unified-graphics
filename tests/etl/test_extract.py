import numpy as np
import pytest
import xarray as xr

from unified_graphics.etl import diag


@pytest.mark.parametrize(
    "filename,variables,loop,init_time,model,system,domain,frequency,background",
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
        ),
        (
            (
                "2a563509-3785-486a-b0d4-2810e3820abf-"
                "RTMA_WCOSS_CONUS_RETRO_diag_uv_ges.202301020400.HRRR.nc4"
            ),
            ["u", "v"],
            "ges",
            "2023-01-02T04:00",
            "RTMA",
            "WCOSS",
            "CONUS",
            "RETRO",
            "HRRR",
        ),
        (
            # In this test the model is missing from the filename It is expected
            # behavior that everything is shifted because we don't do any
            # validation of these values, they are interpreted based on
            # position. Therefore, WCOSS is interpreted as the model, and the
            # frequency ends up as None, despite the fact that it's actually the
            # model that's missing.
            "WCOSS_CONUS_REALTIME_diag_ps_anl.202205051400.HRRR.nc4",
            ["ps"],
            "anl",
            "2022-05-05T14:00",
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
            "2022-05-05T14:00",
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
            "2023-01-02T04:00",
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
    model,
    system,
    domain,
    frequency,
    background,
):
    """diag.parse_diag_filename should return the variable, loop, and
    initialization time from a diag filename
    """
    result = diag.parse_diag_filename(filename)
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
):
    """diag.load should return datasets for observations, forecasts, and results"""

    test_file = diag_file(
        variable, loop, init_time, model, system, domain, frequency, background
    )
    expected_init_time = (
        f"{init_time[:4]}-{init_time[4:6]}-{init_time[6:8]}T{init_time[-2:]}:00"
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

    result = diag.load(test_file)

    xr.testing.assert_equal(result, expected)
    assert result.attrs == expected.attrs


def test_no_forecast_scalar(diag_dataset, tmp_path):
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    frequency = "REALTIME"
    background = "HRRR"
    init_time = "202303171400"
    expected_init_time = "2023-03-17T14:00"
    variable = "ps"
    loop = "ges"

    # FIXME: This test data should be created by a fixture
    filename = (
        f"{model}_{system}_{domain}_{frequency}_"
        f"ncdiag_conv_{variable}_{loop}.{init_time}.{background}.nc4"
    )
    ds = xr.Dataset(
        {
            "Obs_Minus_Forecast_adjusted": (["nobs"], np.zeros((3,))),
            "Obs_Minus_Forecast_unadjusted": (["nobs"], np.zeros((3,))),
            "Observation": (["nobs"], np.zeros((3,))),
            "Analysis_Use_Flag": (["nobs"], np.array([1, -1, 1], dtype=np.int8)),
            "Latitude": (["nobs"], np.array([22, 23, 25], dtype=np.float64)),
            "Longitude": (["nobs"], np.array([90, 91, 200], dtype=np.float64)),
        }
    )
    ds.to_netcdf(tmp_path / filename)

    expected = diag_dataset(
        variable,
        expected_init_time,
        loop,
        model,
        system,
        domain,
        frequency,
        background,
    )

    result = diag.load(tmp_path / filename)

    xr.testing.assert_equal(result, expected)
    assert result.attrs == expected.attrs


def test_no_forecast_vector(diag_dataset, tmp_path):
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    frequency = "REALTIME"
    background = "HRRR"
    init_time = "202303171400"
    expected_init_time = "2023-03-17T14:00"
    variable = "uv"
    loop = "ges"

    # FIXME: This test data should be created by a fixture
    filename = (
        f"{model}_{system}_{domain}_{frequency}_"
        f"ncdiag_conv_{variable}_{loop}.{init_time}.{background}.nc4"
    )
    ds = xr.Dataset(
        {
            "u_Obs_Minus_Forecast_adjusted": (["nobs"], np.zeros((3,))),
            "v_Obs_Minus_Forecast_adjusted": (["nobs"], np.zeros((3,))),
            "u_Obs_Minus_Forecast_unadjusted": (["nobs"], np.zeros((3,))),
            "v_Obs_Minus_Forecast_unadjusted": (["nobs"], np.zeros((3,))),
            "u_Observation": (["nobs"], np.zeros((3,))),
            "v_Observation": (["nobs"], np.zeros((3,))),
            "Analysis_Use_Flag": (["nobs"], np.array([1, -1, 1], dtype=np.int8)),
            "Latitude": (["nobs"], np.array([22, 23, 25], dtype=np.float64)),
            "Longitude": (["nobs"], np.array([90, 91, 200], dtype=np.float64)),
        }
    )
    ds.to_netcdf(tmp_path / filename)

    expected = diag_dataset(
        variable,
        expected_init_time,
        loop,
        model,
        system,
        domain,
        frequency,
        background,
        component=["u", "v"],
    )

    result = diag.load(tmp_path / filename)

    xr.testing.assert_equal(result, expected)
    assert result.attrs == expected.attrs
