from unittest.mock import call, patch
import xarray as xr

from unified_graphics import diag


@patch("xarray.open_dataset")
def test_get_diagnostics(open_dataset_mock):
    ds = xr.Dataset()
    open_dataset_mock.return_value = ds

    result = diag.get_diagnostics()

    open_dataset_mock.assert_has_calls(
        [
            call("data/ncdiag_conv_t_ges.nc4.20220514"),
            call("data/ncdiag_conv_t_anl.nc4.20220514"),
        ],
        any_order=True,
    )

    assert result == (ds, ds)
