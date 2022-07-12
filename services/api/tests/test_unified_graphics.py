from unittest import mock

import xarray as xr


def test_root_endpoint(client):
    response = client.get("/")

    assert response.json == {"msg": "Hello, Dave"}


def test_temperature_diag_distribution(client):
    with mock.patch("xarray.open_dataset") as mock_open_dataset:
        mock_open_dataset.return_value = xr.Dataset(
            {"Obs_Minus_Forecast_adjusted": [-1, 1, 1, 2, 3]}
        )

        response = client.get("/diag/temperature/")

    # FIXME: I don't love asserting these calls to xarray.open_dataset to ensure
    # that the route is looking up both the guess and the analysis diagnostics,
    # it seems like an implementation detail. The alternative seems to be to
    # implement a more complex mock that returns different arrays based on
    # filenames.
    mock_open_dataset.assert_has_calls(
        [
            mock.call("/test/data/ncdiag_conv_t_ges.nc4.2022050514"),
            mock.call("/test/data/ncdiag_conv_t_anl.nc4.2022050514"),
        ],
        any_order=True,
    )

    assert response.json == {
        "guess": {
            "bins": [
                {"lower": -1, "upper": 0, "value": 1},
                {"lower": 0, "upper": 1, "value": 0},
                {"lower": 1, "upper": 2, "value": 2},
                {"lower": 2, "upper": 3, "value": 2},
            ],
            "observations": 5,
            "std": 1.32664991614216,
            "mean": 1.2,
        },
        "analysis": {
            "bins": [
                {"lower": -1, "upper": 0, "value": 1},
                {"lower": 0, "upper": 1, "value": 0},
                {"lower": 1, "upper": 2, "value": 2},
                {"lower": 2, "upper": 3, "value": 2},
            ],
            "observations": 5,
            "std": 1.32664991614216,
            "mean": 1.2,
        },
    }


def test_wind_diag(client):
    response = client.get("/diag/wind/")
    assert response.status_code == 200
