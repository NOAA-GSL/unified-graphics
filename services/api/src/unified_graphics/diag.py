from typing import Tuple
import xarray as xr


# FIXME: typing.Tuple is deprecated in Python 3.9. Once we are off 3.8 in CI, we
# should replace this tuple[xr.Dataset, xr.Dataset]
def get_diagnostics() -> Tuple[xr.Dataset, xr.Dataset]:
    guess = xr.open_dataset("data/ncdiag_conv_t_ges.nc4.20220514")
    analysis = xr.open_dataset("data/ncdiag_conv_t_anl.nc4.20220514")

    return (guess, analysis)
