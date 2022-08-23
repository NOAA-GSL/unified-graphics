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
def test_wind(mock_open_diagnostic):
    # Arrange

    test_dataset = xr.Dataset(
        {
            "Station_ID": xr.DataArray([b"WV270   ", b"E4294   "]),
            "u_Observation": xr.DataArray([0, 0]),
            "u_Obs_Minus_Forecast_adjusted": xr.DataArray([3, 1]),
            "v_Observation": xr.DataArray([10, 10]),
            "v_Obs_Minus_Forecast_adjusted": xr.DataArray([-4, 0]),
            "Longitude": xr.DataArray([240, 272]),
            "Latitude": xr.DataArray([40, 30]),
        }
    )

    mock_open_diagnostic.return_value = test_dataset

    # Act

    data = diag.wind()

    # Assert

    assert mock_open_diagnostic.mock_calls == [
        mock.call(diag.Variable.WIND, diag.MinimLoop.GUESS),
        mock.call(diag.Variable.WIND, diag.MinimLoop.ANALYSIS),
    ]

    assert data == [
        diag.VectorObservation(
            stationId="WV270",
            variable="wind",
            guess=diag.PolarCoordinate(5.0, 323.13010235415595),
            analysis=diag.PolarCoordinate(5.0, 323.13010235415595),
            observed=diag.PolarCoordinate(10.0, 180.0),
            position=diag.Coordinate(-120.0, 40.0),
        ),
        diag.VectorObservation(
            stationId="E4294",
            variable="wind",
            guess=diag.PolarCoordinate(1.0, 270.0),
            analysis=diag.PolarCoordinate(1.0, 270.0),
            observed=diag.PolarCoordinate(10.0, 180.0),
            position=diag.Coordinate(-88.0, 30.0),
        ),
    ]


def test_VectorObservation_to_geojson():
    subject = diag.VectorObservation(
        "WV270",
        "wind",
        diag.PolarCoordinate(1, 180),
        diag.PolarCoordinate(0.5, 0),
        diag.PolarCoordinate(1, 90),
        diag.Coordinate(0, 0),
    )

    result = subject.to_geojson()

    assert result == {
        "type": "Feature",
        "properties": {
            "stationId": "WV270",
            "variable": "wind",
            "guess": {"magnitude": 1, "direction": 180},
            "analysis": {"magnitude": 0.5, "direction": 0},
            "observed": {"magnitude": 1, "direction": 90},
        },
        "geometry": {"type": "Point", "coordinates": [0, 0]},
    }
