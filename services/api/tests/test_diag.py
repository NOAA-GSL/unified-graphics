from pathlib import Path
from unittest import mock

import pytest
import xarray as xr

from unified_graphics import diag


@pytest.fixture
def make_scalar_diag():
    def _make_scalar_diag(omf):
        return xr.Dataset(
            {
                "Obs_Minus_Forecast_unadjusted": omf,
            }
        )

    return _make_scalar_diag


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (diag.MinimLoop.GUESS, "ncdiag_conv_t_ges.nc4.2022050514"),
        (diag.MinimLoop.ANALYSIS, "ncdiag_conv_t_anl.nc4.2022050514"),
    ],
)
def test_get_diag_filepath(tmp_path, app, test_input, expected):
    with app.app_context():
        result = diag.get_filepath(test_input)

    assert result == str(tmp_path / "data" / expected)


def test_get_diagnostics(app):
    with mock.patch("xarray.open_dataset") as mock_open_dataset:
        mock_open_dataset.return_value = xr.Dataset(
            {"Obs_Minus_Forecast_adjusted": [-1, 1, 1, 2, 3]}
        )

        with app.app_context():
            result = diag.get_diagnostics(diag.MinimLoop.GUESS)

    assert result == {
        "bins": [
            {"lower": -1, "upper": 0, "value": 1},
            {"lower": 0, "upper": 1, "value": 0},
            {"lower": 1, "upper": 2, "value": 2},
            {"lower": 2, "upper": 3, "value": 2},
        ],
        "observations": 5,
        "std": 1.32664991614216,
        "mean": 1.2,
    }


@pytest.mark.parametrize(
    "variable,loop,filename",
    [
        (
            diag.Variable.MOISTURE,
            diag.MinimLoop.GUESS,
            "ncdiag_conv_q_ges.nc4.2022050514",
        ),
        (
            diag.Variable.PRESSURE,
            diag.MinimLoop.ANALYSIS,
            "ncdiag_conv_p_anl.nc4.2022050514",
        ),
        (
            diag.Variable.TEMPERATURE,
            diag.MinimLoop.ANALYSIS,
            "ncdiag_conv_t_anl.nc4.2022050514",
        ),
        (diag.Variable.WIND, diag.MinimLoop.GUESS, "ncdiag_conv_uv_ges.nc4.2022050514"),
    ],
)
def test_open_diagnostic(variable, loop, filename, app, make_scalar_diag):
    diag_dir = Path(app.config["DIAG_DIR"])
    expected = make_scalar_diag(omf=[0, -1, 2])
    expected.to_netcdf(diag_dir / filename)

    with app.app_context():
        result = diag.open_diagnostic(variable, loop)

    xr.testing.assert_equal(result, expected)


def test_open_diagnostic_does_not_exist(app):
    expected = r"No such file: '.*ncdiag_conv_uv_ges.nc4.2022050514'$"

    with app.app_context():
        with pytest.raises(FileNotFoundError, match=expected):
            diag.open_diagnostic(diag.Variable.WIND, diag.MinimLoop.GUESS)


@pytest.mark.xfail
def test_open_diagnostic_unknown_backend():
    assert 0


@mock.patch("unified_graphics.diag.VectorVariable", autospec=True)
@mock.patch("unified_graphics.diag.VectorDiag", autospec=True)
@mock.patch("unified_graphics.diag.open_diagnostic", autospec=True)
def test_wind(mock_open_diagnostic, mock_VectorDiag, mock_VectorVariable):
    test_dataset = xr.Dataset(
        {
            "u_Observation": xr.DataArray([0, 0]),
            "u_Obs_Minus_Forecast_unadjusted": xr.DataArray([1, 1]),
            "v_Observation": xr.DataArray([10, 10]),
            "v_Obs_Minus_Forecast_unadjusted": xr.DataArray([-5, 5]),
        }
    )
    mock_open_diagnostic.return_value = test_dataset
    expected = diag.VectorDiag(
        observation=diag.VectorVariable(direction=[0, 135], magnitude=[1, 2]),
        forecast=diag.VectorVariable(direction=[25, 130], magnitude=[2, 1]),
    )

    mock_VectorDiag.return_value = expected

    data = diag.wind(diag.MinimLoop.GUESS)

    mock_open_diagnostic.assert_called_once_with(
        diag.Variable.WIND, diag.MinimLoop.GUESS
    )
    calls = mock_VectorVariable.from_vectors.call_args_list

    assert len(calls) == 2

    # We can't use from_vectors.assert_has_calls because the default comparison
    # of two xarray.DataArray objects via `==` results in a DataArray containing
    # boolean values indiciating whether each pairwise element were equal or
    # not. Instead we use the xarray.testing assertions.

    # Assert that a VectorVariable was created from the observed vectors
    xr.testing.assert_equal(calls[0].args[0], xr.DataArray([0, 0]))
    xr.testing.assert_equal(calls[0].args[1], xr.DataArray([10, 10]))

    # Assert that a VectorVariable was created from forecast vectors that were
    # calculated by subtracting Obs-Fcst from Obs: Obs - (Obs - Fcst) = Fcst
    xr.testing.assert_equal(calls[1].args[0], xr.DataArray([-1, -1]))
    xr.testing.assert_equal(calls[1].args[1], xr.DataArray([15, 5]))

    assert data == expected


@pytest.mark.xfail
@mock.patch("unified_graphics.diag.VectorVariable", autospec=True)
@mock.patch("unified_graphics.diag.VectorDiag", autospec=True)
@mock.patch("unified_graphics.diag.open_diagnostic", autospec=True)
def test_wind_diag_does_not_exist(
    mock_open_diagnostic, mock_VectorDiag, mock_VectorVariable
):
    assert 0
