import xarray as xr


def load(path: str) -> xr.Dataset:
    """Load the diagnostic file at `path` into an xarray DataSet

    Load the diagnostic file and convert the fields to the format used by the
    Unified Graphics backend.

    Parameters
    ----------
    path : str
        The path to a NetCDF4 file on the filesystem

    Returns
    -------
    xarray.Dataset
        The diagnostic data converted to an xarray Dataset
    """
    ...
