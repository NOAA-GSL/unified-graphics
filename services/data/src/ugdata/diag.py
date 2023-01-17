def to_zarr(path: str, upload_bucket: str):
    """Convert the NetCDF4 file at `path` to a Zarr array in `upload_bucket`

    Parameters
    ----------
    path : str
        The path to a NetCDF4 file on the filesystem
    upload_bucket : str
        The name of an S3 bucket to which the Zarr will be written
    """
    ...
