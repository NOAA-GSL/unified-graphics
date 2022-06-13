from unified_graphics import diag

from unittest.mock import call, patch


@patch("xarray.open_dataset")
def test_get_diagnostics(open_dataset_mock):
    diag.get_diagnostics()

    open_dataset_mock.assert_has_calls(
        [
            call("data/ncdiag_conv_t_ges.nc4.20220514"),
            call("data/ncdiag_conv_t_anl.nc4.20220514"),
        ],
        any_order=True,
    )
