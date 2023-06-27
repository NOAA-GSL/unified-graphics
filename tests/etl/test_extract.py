from typing import Optional

import numpy as np
import pytest
import xarray as xr

from unified_graphics.etl import diag


@pytest.fixture(scope="module")
def input_data():
    def _input_data(
        *,
        Forecast_adjusted,
        Forecast_unadjusted,
        Observation,
        Analysis_Use_Flag,
        Latitude,
        Longitude,
    ):
        return xr.Dataset(
            {
                "Forecast_adjusted": (["nobs"], Forecast_adjusted),
                "Forecast_unadjusted": (["nobs"], Forecast_unadjusted),
                "Obs_Minus_Forecast_adjusted": (
                    ["nobs"],
                    Observation - Forecast_adjusted,
                ),
                "Obs_Minus_Forecast_unadjusted": (
                    ["nobs"],
                    Observation - Forecast_unadjusted,
                ),
                "Observation": (["nobs"], Observation),
                "Analysis_Use_Flag": (["nobs"], Analysis_Use_Flag),
                "Latitude": (["nobs"], Latitude),
                "Longitude": (["nobs"], Longitude),
            }
        )

    return _input_data


@pytest.fixture(scope="class")
def netcdf_path(tmp_path_factory):
    def _netcdf_path(
        variable: str,
        loop: str,
        init_time: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        domain: Optional[str] = None,
        frequency: Optional[str] = None,
        background: Optional[str] = None,
    ):
        path = tmp_path_factory.mktemp("diag_netcdf")

        filename = f"ncdiag_conv_{variable}_{loop}.{init_time}"
        if background:
            filename += "." + background
        filename += ".nc4"

        prefix = "_".join(filter(None, (model, system, domain, frequency)))

        return path / "_".join(filter(None, (prefix, filename)))

    return _netcdf_path


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
    "variable,loop,init_time,model,system,domain,frequency,background",
    [
        ("q", "anl", "2022050514", None, None, None, None, None),
        ("q", "anl", "2022050514", "RTMA", "WCOSS", "CONUS", "REALTIME", "HRRR"),
    ],
    scope="class",
)
class TestLoad:
    """diag.load should return datasets for observations, forecasts, and results"""

    @pytest.fixture(scope="class")
    def test_file(
        self,
        variable,
        loop,
        init_time,
        model,
        system,
        domain,
        frequency,
        background,
        input_data,
        netcdf_path,
    ):
        ds = input_data(
            Forecast_adjusted=np.array([0, 1]),
            Forecast_unadjusted=np.array([0, 1]),
            Observation=np.array([1, 0]),
            Analysis_Use_Flag=np.array([1, -1]),
            Latitude=np.array([22, 23]),
            Longitude=np.array([90, 91]),
        )

        path = netcdf_path(
            variable, loop, init_time, model, system, domain, frequency, background
        )

        ds.to_netcdf(path)

        return path

    @pytest.fixture
    def expected(
        self,
        variable,
        loop,
        init_time,
        model,
        system,
        domain,
        frequency,
        background,
        test_dataset,
    ):
        expected_init_time = (
            f"{init_time[:4]}-{init_time[4:6]}-{init_time[6:8]}T{init_time[-2:]}:00"
        )
        return test_dataset(
            model=model or "Unknown",
            system=system or "Unknown",
            domain=domain or "Unknown",
            background=background or "Unknown",
            frequency=frequency or "Unknown",
            initialization_time=expected_init_time,
            variable=variable,
            loop=loop,
        )

    @pytest.fixture(scope="class")
    def result(self, test_file):
        return diag.load(test_file)

    def test_datasets(self, result, expected):
        xr.testing.assert_equal(result, expected)

    def test_attributes(self, result, expected):
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
