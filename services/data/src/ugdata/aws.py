import os
import uuid
from pathlib import Path

import boto3  # type: ignore

from . import diag

s3_client = boto3.client("s3")


def fetch_record(bucket: str, key: str, download_path: str = "/tmp") -> Path:
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
    pathlib.Path
        The path to the downloaded file
    """
    tmp_key = key.replace("/", "_")
    tmp_path = Path(download_path) / f"{uuid.uuid4()}-{tmp_key}"
    s3_client.download_file(bucket, key, tmp_path)
    return tmp_path


def lambda_handler(event, context):
    """Handler for Lambda events."""

    upload_bucket = os.environ["UG_UPLOAD_BUCKET"]

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        tmp_file = fetch_record(bucket, key)

        data = diag.load(tmp_file)
        diag.save(upload_bucket, *data)
