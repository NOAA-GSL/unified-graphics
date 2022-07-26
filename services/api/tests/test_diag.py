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


@mock.patch("unified_graphics.diag.ScalarDiag", autospec=True)
@mock.patch("unified_graphics.diag.open_diagnostic", autospec=True)
@pytest.mark.parametrize("loop", ([diag.MinimLoop.GUESS], [diag.MinimLoop.ANALYSIS]))
def test_temperature(mock_open_diagnostic, mock_ScalarDiag, loop):
    expected = diag.ScalarDiag(
        bins=[diag.Bin(lower=-1, upper=1, value=3)], observations=10, std=1.2, mean=0.3
    )

    mock_open_diagnostic.return_value = xr.Dataset(
        {"Obs_Minus_Forecast_adjusted": xr.DataArray([1, 3, 5])}
    )
    mock_ScalarDiag.from_array.return_value = expected

    result = diag.temperature(loop)

    mock_open_diagnostic.assert_called_once_with(diag.Variable.TEMPERATURE, loop)
    mock_ScalarDiag.from_array.assert_called_once()
    xr.testing.assert_equal(
        mock_ScalarDiag.from_array.call_args_list[0].args[0], xr.DataArray([1, 3, 5])
    )

    assert result == expected


@mock.patch("unified_graphics.diag.ScalarDiag", autospec=True)
@mock.patch("unified_graphics.diag.open_diagnostic", autospec=True)
def test_temperature_diag_does_not_exist(mock_open_diagnostic, mock_ScalarDiag):
    mock_open_diagnostic.side_effect = FileNotFoundError()

    with pytest.raises(FileNotFoundError):
        diag.temperature(diag.MinimLoop.GUESS)

    mock_ScalarDiag.from_array.assert_not_called()


@mock.patch("unified_graphics.diag.ScalarDiag", autospec=True)
@mock.patch("unified_graphics.diag.open_diagnostic", autospec=True)
def test_temperature_diag_unknown_backend(mock_open_diagnostic, mock_ScalarDiag):
    mock_open_diagnostic.side_effect = ValueError()

    with pytest.raises(ValueError):
        diag.temperature(diag.MinimLoop.GUESS)

    mock_ScalarDiag.from_array.assert_not_called()


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


@mock.patch("unified_graphics.diag.open_diagnostic", autospec=True)
@mock.patch("unified_graphics.diag.VectorVariable", autospec=True)
@pytest.mark.parametrize(
    "value_type,expected_u,expected_v",
    [
        (diag.ValueType.OBSERVATION, xr.DataArray([0, 0]), xr.DataArray([10, 10])),
        (diag.ValueType.FORECAST, xr.DataArray([-1, -1]), xr.DataArray([15, 5])),
    ],
)
def test_wind(
    mock_VectorVariable, mock_open_diagnostic, value_type, expected_u, expected_v
):
    test_dataset = xr.Dataset(
        {
            "u_Observation": xr.DataArray([0, 0]),
            "u_Obs_Minus_Forecast_unadjusted": xr.DataArray([1, 1]),
            "v_Observation": xr.DataArray([10, 10]),
            "v_Obs_Minus_Forecast_unadjusted": xr.DataArray([-5, 5]),
            "Longitude": xr.DataArray([-120, -88]),
            "Latitude": xr.DataArray([40, 30]),
        }
    )

    mock_open_diagnostic.return_value = test_dataset

    # Do the thing!
    data = diag.wind(diag.MinimLoop.GUESS, value_type)

    mock_open_diagnostic.assert_called_once_with(
        diag.Variable.WIND, diag.MinimLoop.GUESS
    )

    # We can't use from_vectors.assert_has_calls because the default comparison
    # of two xarray.DataArray objects via `==` results in a DataArray containing
    # boolean values indiciating whether each pairwise element were equal or
    # not. Instead we use the xarray.testing assertions.

    # Check calls to VectorVariable.from_vectors
    mock_VectorVariable.from_vectors.assert_called_once()
    VectorVariable_calls = mock_VectorVariable.from_vectors.call_args_list[0].args

    # Assert that a VectorVariable was created from the observed vectors with
    # coordinates
    xr.testing.assert_equal(VectorVariable_calls[0], expected_u)
    xr.testing.assert_equal(VectorVariable_calls[1], expected_v)
    xr.testing.assert_equal(VectorVariable_calls[2], xr.DataArray([-120, -88]))
    xr.testing.assert_equal(VectorVariable_calls[3], xr.DataArray([40, 30]))

    assert data == mock_VectorVariable.from_vectors.return_value


@mock.patch("unified_graphics.diag.VectorVariable", autospec=True)
@mock.patch("unified_graphics.diag.open_diagnostic", autospec=True)
def test_wind_diag_does_not_exist(mock_open_diagnostic, mock_VectorVariable):
    mock_open_diagnostic.side_effect = FileNotFoundError()

    with pytest.raises(FileNotFoundError):
        diag.wind(diag.MinimLoop.GUESS, diag.ValueType.OBSERVATION)

    mock_VectorVariable.from_vectors.assert_not_called()


@mock.patch("unified_graphics.diag.VectorVariable", autospec=True)
@mock.patch("unified_graphics.diag.open_diagnostic", autospec=True)
def test_wind_diag_unknown_backend(mock_open_diagnostic, mock_VectorVariable):
    mock_open_diagnostic.side_effect = ValueError()

    with pytest.raises(ValueError):
        diag.wind(diag.MinimLoop.GUESS, diag.ValueType.OBSERVATION)

    mock_VectorVariable.from_vectors.assert_not_called()


def test_coordinate_pairs_from_vector():
    lng = xr.DataArray([-120, -110.08, -90])
    lat = xr.DataArray([40.2, 35, 37])

    result = diag.coordinate_pairs_from_vectors(lng, lat)

    assert result == [
        diag.Coordinate(longitude=-120.0, latitude=40.2),
        diag.Coordinate(longitude=-110.08, latitude=35.0),
        diag.Coordinate(longitude=-90.0, latitude=37.0),
    ]


def test_coordinate_pairs_from_empty_vectors():
    result = diag.coordinate_pairs_from_vectors(xr.DataArray([]), xr.DataArray([]))
    assert result == []


@pytest.mark.parametrize(
    "lng,lat",
    [
        ([0, 1], [1]),
        ([1], [0, 1]),
    ],
)
def test_coordinate_pairs_from_mismatched_vectors(lng, lat):
    with pytest.raises(AssertionError):
        diag.coordinate_pairs_from_vectors(xr.DataArray(lng), xr.DataArray(lat))


def test_ScalarDiag_from_array():
    data = xr.DataArray([10.0, 8.0, 13.0, 9.0, 11.0, 14.0, 6.0, 4.0, 12.0, 7.0, 5.0])
    expected_obs = len(data)
    expected_mean = sum(data) / expected_obs
    expected_std = math.sqrt(
        sum([(x - expected_mean) ** 2 for x in data]) / expected_obs
    )

    result = diag.ScalarDiag.from_array(data)

    assert result == diag.ScalarDiag(
        bins=[
            diag.Bin(lower=4, upper=6, value=2),
            diag.Bin(lower=6, upper=8, value=2),
            diag.Bin(lower=8, upper=10, value=2),
            diag.Bin(lower=10, upper=12, value=2),
            diag.Bin(lower=12, upper=14, value=3),
        ],
        observations=expected_obs,
        mean=expected_mean,
        std=expected_std,
    )


def test_ScalarDiag_from_zeros():
    data = xr.DataArray([0, 0, 0, 0])

    result = diag.ScalarDiag.from_array(data)

    assert result == diag.ScalarDiag(
        bins=[diag.Bin(lower=-0.5, upper=0.5, value=4)], observations=4, mean=0, std=0
    )


def test_ScalarDiag_from_empty_array():
    result = diag.ScalarDiag.from_array(xr.DataArray([]))

    assert result == diag.ScalarDiag(bins=[], observations=0, mean=0, std=0)


def test_VectorVariable_from_vectors():
    u = xr.DataArray([0, 2, 0, -1, -1])
    v = xr.DataArray([1, 0, -2, 0, 1])
    lng = xr.DataArray([0] * 5)
    lat = xr.DataArray([1] * 5)

    result = diag.VectorVariable.from_vectors(u, v, lng, lat)

    assert result == diag.VectorVariable(
        direction=[180.0, 270.0, 0.0, 90.0, 135.0],
        magnitude=[1.0, 2.0, 2.0, 1.0, math.sqrt(2)],
        coords=[diag.Coordinate(0, 1)] * 5,
    )


def test_VectorVariable_from_vectors_calm():
    # 0.0 != -0.0, and numpy.arctan2 will return a different angle depending on
    # which one it encounters in which of the two vector components. We want to
    # make sure we normalize the direction for all vectors of magnitude 0 to be
    # 0°.
    u = xr.DataArray([0.0, -0.0, 0.0, -0.0])
    v = xr.DataArray([0.0, 0.0, -0.0, -0.0])
    lng = xr.DataArray([0] * 4)
    lat = xr.DataArray([1] * 4)

    result = diag.VectorVariable.from_vectors(u, v, lng, lat)

    assert result == diag.VectorVariable(
        direction=[0.0, 0.0, 0.0, 0.0],
        magnitude=[0.0, 0.0, 0.0, 0.0],
        coords=[diag.Coordinate(0, 1)] * 4,
    )


def test_VectorVariable_from_empty_vectors():
    u = xr.DataArray([])
    v = xr.DataArray([])
    lng = xr.DataArray([])
    lat = xr.DataArray([])

    result = diag.VectorVariable.from_vectors(u, v, lng, lat)

    assert result == diag.VectorVariable(direction=[], magnitude=[], coords=[])


@pytest.mark.parametrize(
    "u,v,lng,lat",
    (
        ([0, 1], [1], [1], [1]),
        ([1], [0, 1], [1], [1]),
        ([1], [1], [0, 1], [1]),
        ([1], [1], [1], [0, 1]),
        ([1], [1], [0, 1], [0, 1]),
    ),
)
def test_VectorVariable_from_mismatched_vectors(u, v, lng, lat):
    with pytest.raises(AssertionError):
        diag.VectorVariable.from_vectors(
            xr.DataArray(u), xr.DataArray(v), xr.DataArray(lng), xr.DataArray(lat)
        )
