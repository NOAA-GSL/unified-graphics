import os

from . import diag


def fetch_record(bucket: str, key: str, download_path: str = "/tmp") -> str:
    """Download a NetCDF file from S3

    Parameters
    ----------
    bucket : str
        The name of the S3 bucket
    key : str
        The object key in S3
    download_path : str
        The location to which the file will be downloaded (default is "/tmp")

    Returns
    -------
    str
        The path to the downloaded file
    """
    ...


def lambda_handler(event, context):
    """Handler for Lambda events."""

    upload_bucket = os.environ["UG_UPLOAD_BUCKET"]

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        tmp_file = fetch_record(bucket, key)

        data = diag.load(tmp_file)
        diag.save(upload_bucket, *data)
