import pytest
import xarray as xr

from unified_graphics import diag


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (diag.MinimLoop.GUESS, "/test/data/ncdiag_conv_t_ges.nc4.2022050514"),
        (diag.MinimLoop.ANALYSIS, "/test/data/ncdiag_conv_t_anl.nc4.2022050514"),
    ],
)
def test_get_diag_filepath(app, test_input, expected):
    with app.app_context():
        result = diag.get_filepath(test_input)

    assert result == expected


def test_get_diagnostics(app, monkeypatch):
    def mock_open_dataset(*args, **kwargs):
        return xr.Dataset({"Obs_Minus_Forecast_adjusted": [-1, 1, 1, 2, 3]})

    monkeypatch.setattr(xr, "open_dataset", mock_open_dataset)

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
