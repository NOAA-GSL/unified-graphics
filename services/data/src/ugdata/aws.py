import gzip
import os
import shutil
import uuid
from pathlib import Path
from urllib.parse import unquote_plus

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
    s3_client.download_file(bucket, key, str(tmp_path))

    if tmp_path.suffix != ".gz":
        return tmp_path

    decompressed_path = tmp_path.with_name(tmp_path.stem)

    with gzip.open(tmp_path, "rb") as f_in:
        with open(decompressed_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    return decompressed_path


def lambda_handler(event, context):
    """Handler for Lambda events."""

    if "Event" in event and event["Event"] == "s3:TestEvent":
        return "Test event received"

    if (
        "detail" not in event
        or "bucket" not in event["detail"]
        or "object" not in event["detail"]
    ):
        # FIXME: This should use a real logger
        print("Object details missing from event")
        print(event)
        return ""

    upload_bucket = os.environ["UG_DIAG_ZARR"]

    bucket = event["detail"]["bucket"]["name"]
    key = unquote_plus(event["detail"]["object"]["key"])

    # Only fetch the first (ges) and last (anl) minimization loops, ignore
    # all intermediate loops.
    if diag.parse_diag_filename(key.replace("/", "_")).loop not in ["anl", "ges"]:
        print(f"Skipping loop: {key}")
        return ""

    tmp_file = fetch_record(bucket, key)

    data = diag.load(tmp_file)
    diag.save(upload_bucket, data)
