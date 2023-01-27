"""Test saving xarray Datasets to Zarr"""

import xarray as xr
from ugdata import diag


def test_save_new(tmp_path, diag_dataset):
    """diag.save should create a new Zarr on first write"""

    init_time = "2022-05-05T14"
    loop = "anl"

    difference = diag_dataset("difference", ["ps"], init_time, loop, is_adjusted=[0, 1])
    forecast = diag_dataset("forecast", ["ps"], init_time, loop, is_adjusted=[0, 1])
    observations = diag_dataset("observations", ["ps"], init_time, loop)

    zarr_file = tmp_path / "unified_graphics.zarr"
    diag.save(zarr_file, difference, forecast, observations)

    assert zarr_file.exists(), "Zarr file not created"
    assert (
        zarr_file / "difference" / init_time / loop
    ).exists(), "Difference group is missing"
    assert (
        zarr_file / "forecast" / init_time / loop
    ).exists(), "Forecast group is missing"
    assert (
        zarr_file / "observations" / init_time / loop
    ).exists(), "Observations group is missing"

    xr.testing.assert_equal(
        xr.open_zarr(zarr_file, group=f"difference/{init_time}/{loop}"), difference
    )
    xr.testing.assert_equal(
        xr.open_zarr(zarr_file, group=f"forecast/{init_time}/{loop}"), forecast
    )
    xr.testing.assert_equal(
        xr.open_zarr(zarr_file, group=f"observations/{init_time}/{loop}"), observations
    )
