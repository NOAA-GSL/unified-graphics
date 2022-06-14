import xarray as xr

from unified_graphics import diag


def test_get_diag_filepath(app):
    with app.app_context():
        result = diag.get_filepath(diag.MinimLoop.GUESS)

    assert result == "/test/data/ncdiag_conv_t_ges.nc4.20220514"


def test_get_diagnostics(monkeypatch):
    def mock_open_dataset(*args, **kwargs):
        return xr.Dataset({"Obs_Minus_Forecast_adjusted": [-1, 1, 1, 2, 3]})

    monkeypatch.setattr(xr, "open_dataset", mock_open_dataset)
    result = diag.get_diagnostics()

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
