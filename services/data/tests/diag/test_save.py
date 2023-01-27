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


def test_add_loop(diag_zarr, diag_dataset):
    """diag.save should add a new group for each loop"""

    variables = ["ps"]
    init_time = "2022-05-05T14"
    zarr_file = diag_zarr(variables, "anl", init_time)

    loop = "ges"
    difference = diag_dataset(
        "difference", variables, init_time, loop, is_adjusted=[0, 1]
    )
    forecast = diag_dataset("forecast", variables, init_time, loop, is_adjusted=[0, 1])
    observations = diag_dataset("observations", variables, init_time, loop)

    diag.save(zarr_file, observations, forecast, difference)

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


def test_add_variable(diag_zarr, diag_dataset):
    """diag.save should insert new variables into existing groups"""

    init_time = "2022-05-05T14"
    loop = "anl"
    zarr_file = diag_zarr(["ps"], init_time, loop)

    difference = diag_dataset("difference", ["t"], init_time, loop, is_adjusted=[0, 1])
    forecast = diag_dataset("forecast", ["t"], init_time, loop, is_adjusted=[0, 1])
    observations = diag_dataset("observations", ["t"], init_time, loop)

    diag.save(zarr_file, observations, forecast, difference)

    xr.testing.assert_equal(
        xr.open_zarr(zarr_file, group=f"/difference/{init_time}/{loop}"),
        diag_dataset("difference", ["ps", "t"], init_time, loop, is_adjusted=[0, 1]),
    )
    xr.testing.assert_equal(
        xr.open_zarr(zarr_file, group=f"/forecast/{init_time}/{loop}"),
        diag_dataset("forecast", ["ps", "t"], init_time, loop, is_adjusted=[0, 1]),
    )
    xr.testing.assert_equal(
        xr.open_zarr(zarr_file, group=f"/observations/{init_time}/{loop}"),
        diag_dataset("observations", ["ps", "t"], init_time, loop),
    )
