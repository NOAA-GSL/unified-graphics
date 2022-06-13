import xarray as xr


def get_diagnostics() -> tuple[xr.Dataset, xr.Dataset]:
    guess: xr.Dataset = xr.open_dataset("data/ncdiag_conv_t_ges.nc4.20220514")
    analysis: xr.Dataset = xr.open_dataset("data/ncdiag_conv_t_anl.nc4.20220514")

    return (guess, analysis)
