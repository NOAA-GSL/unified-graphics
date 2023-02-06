"""Test saving xarray Datasets to Zarr"""

import xarray as xr
from ugdata import diag


def test_save_new(tmp_path, diag_dataset):
    """diag.save should create a new Zarr on first write"""

    init_time = "2022-05-05T14"
    loop = "anl"

    ps = diag_dataset("ps", init_time, loop)

    zarr_file = tmp_path / "unified_graphics.zarr"
    diag.save(zarr_file, ps)

    assert zarr_file.exists(), "Zarr file not created"
    assert (zarr_file / "ps").exists(), "variable group is missing"
    assert (
        zarr_file / "ps" / init_time
    ).exists(), "initialization time group is missing"
    assert (zarr_file / "ps" / init_time / loop).exists(), "loop group is missing"

    xr.testing.assert_equal(xr.open_zarr(zarr_file, group=f"ps/{init_time}/{loop}"), ps)


def test_add_loop(diag_zarr, diag_dataset):
    """diag.save should add a new group for each loop"""

    variables = ["ps"]
    init_time = "2022-05-05T14"
    zarr_file = diag_zarr(variables, "anl", init_time)

    loop = "ges"
    ps = diag_dataset(variables[0], init_time, loop)

    diag.save(zarr_file, ps)

    assert (zarr_file / "ps" / init_time / loop).exists(), "Loop group is missing"

    xr.testing.assert_equal(
        xr.open_zarr(zarr_file, group=f"{variables[0]}/{init_time}/{loop}"), ps
    )


def test_add_variable(diag_zarr, diag_dataset):
    """diag.save should insert new variables into existing groups"""

    init_time = "2022-05-05T14"
    loop = "anl"
    zarr_file = diag_zarr(["ps"], init_time, loop)

    t = diag_dataset("t", init_time, loop)

    diag.save(zarr_file, t)

    xr.testing.assert_equal(
        xr.open_zarr(zarr_file, group=f"/t/{init_time}/{loop}"),
        diag_dataset("t", init_time, loop),
    )