import xarray as xr


def get_diagnostics():
    xr.open_dataset("data/ncdiag_conv_t_ges.nc4.20220514")
    xr.open_dataset("data/ncdiag_conv_t_anl.nc4.20220514")
