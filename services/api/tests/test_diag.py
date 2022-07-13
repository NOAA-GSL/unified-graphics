from pathlib import Path
from unittest import mock

import math
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


@mock.patch("unified_graphics.diag.open_diagnostic", autospec=True)
@pytest.mark.parametrize("loop", ([diag.MinimLoop.GUESS], [diag.MinimLoop.ANALYSIS]))
def test_temperature(mock_open_diagnostic, loop):
    diag.temperature(loop)

    mock_open_diagnostic.assert_called_once_with(diag.Variable.TEMPERATURE, loop)


@pytest.mark.xfail
def test_temperature_diag_does_not_exist():
    assert 0


@pytest.mark.xfail
def test_temperature_diag_unknown_backend():
    assert 0


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


def test_open_diagnostic_unknown_backend(app):
    diag_dir = Path(app.config["DIAG_DIR"])
    test_file = diag_dir / "ncdiag_conv_uv_ges.nc4.2022050514"
    test_file.write_bytes(b"This is not a NetCDF4 file")

    expected = (
        r"did not find a match in any of xarray's currently installed IO backends.*"
    )

    with app.app_context():
        with pytest.raises(ValueError, match=expected):
            diag.open_diagnostic(diag.Variable.WIND, diag.MinimLoop.GUESS)


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


@mock.patch("unified_graphics.diag.VectorVariable", autospec=True)
@mock.patch("unified_graphics.diag.VectorDiag", autospec=True)
@mock.patch("unified_graphics.diag.open_diagnostic", autospec=True)
def test_wind_diag_does_not_exist(
    mock_open_diagnostic, mock_VectorDiag, mock_VectorVariable
):
    mock_open_diagnostic.side_effect = FileNotFoundError()

    with pytest.raises(FileNotFoundError):
        diag.wind(diag.MinimLoop.GUESS)

    mock_VectorVariable.from_vectors.assert_not_called()
    mock_VectorDiag.assert_not_called()


@mock.patch("unified_graphics.diag.VectorVariable", autospec=True)
@mock.patch("unified_graphics.diag.VectorDiag", autospec=True)
@mock.patch("unified_graphics.diag.open_diagnostic", autospec=True)
def test_wind_diag_unknown_backend(
    mock_open_diagnostic, mock_VectorDiag, mock_VectorVariable
):
    mock_open_diagnostic.side_effect = ValueError()

    with pytest.raises(ValueError):
        diag.wind(diag.MinimLoop.GUESS)

    mock_VectorVariable.from_vectors.assert_not_called()
    mock_VectorDiag.assert_not_called()


def test_VectorVariable_from_vectors():
    u = xr.DataArray([0, 2, 0, -1, -1])
    v = xr.DataArray([1, 0, -2, 0, 1])

    result = diag.VectorVariable.from_vectors(u, v)

    assert result == diag.VectorVariable(
        direction=[180.0, 270.0, 0.0, 90.0, 135.0],
        magnitude=[1.0, 2.0, 2.0, 1.0, math.sqrt(2)],
    )


def test_VectorVariable_from_vectors_calm():
    # 0.0 != -0.0, and numpy.arctan2 will return a different angle depending on
    # which one it encounters in which of the two vector components. We want to
    # make sure we normalize the direction for all vectors of magnitude 0 to be
    # 0°.
    u = xr.DataArray([0.0, -0.0, 0.0, -0.0])
    v = xr.DataArray([0.0, 0.0, -0.0, -0.0])

    result = diag.VectorVariable.from_vectors(u, v)

    assert result == diag.VectorVariable(
        direction=[0.0, 0.0, 0.0, 0.0],
        magnitude=[0.0, 0.0, 0.0, 0.0],
    )


def test_VectorVariable_from_empty_vectors():
    u = xr.DataArray([])
    v = xr.DataArray([])

    result = diag.VectorVariable.from_vectors(u, v)

    assert result == diag.VectorVariable(direction=[], magnitude=[])


def test_VectorVariable_from_mismatched_vectors():
    u = xr.DataArray([0, 1])
    v = xr.DataArray([1])

    with pytest.raises(ValueError):
        diag.VectorVariable.from_vectors(u, v)
