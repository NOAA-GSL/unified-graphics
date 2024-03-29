import gzip
import logging
import os
import shutil
import uuid
from pathlib import Path
from urllib.parse import unquote_plus

import boto3  # type: ignore
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from . import diag

s3_client = boto3.client("s3")

# Logger setup
# Lambda has a default logger configured that we want to override so we can
# configure our own
logging.basicConfig(
    level=logging.DEBUG if os.environ.get("DEBUG", False) else logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",  # ISO 8601
    force=True,  # Override AWS's default logger
)
logger = logging.getLogger(__name__)


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
    key_prefix = os.environ.get("UG_DIAG_KEY_PREFIX")
    tmp_key = key.removeprefix(key_prefix).removeprefix("/") if key_prefix else key
    tmp_key = tmp_key.replace("/", "_")

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

    logger.info(f"Processing event: {event}")

    if "Event" in event and event["Event"] == "s3:TestEvent":
        return "Test event received"

    if (
        "detail" not in event
        or "bucket" not in event["detail"]
        or "object" not in event["detail"]
    ):
        logger.warning("Object details missing from event {event}")
        return ""

    zarr_upload = os.environ["UG_DIAG_ZARR"]
    parquet_upload = os.environ["UG_DIAG_PARQUET"]

    bucket = event["detail"]["bucket"]["name"]
    key = unquote_plus(event["detail"]["object"]["key"])

    logger.info(f"Started processing {bucket}:{key}")

    # Only fetch the first (ges) and last (anl) minimization loops, ignore
    # all intermediate loops.
    if diag.parse_diag_filename(key.replace("/", "_")).loop not in ["anl", "ges"]:
        logger.info(f"Skipping loop: {key}")
        return ""

    logger.info(f"Fetching record {bucket}:{key} to disk")
    tmp_file = fetch_record(bucket, key)

    logger.info(f"Loading {bucket}:{key} from disk into memory")
    data = diag.load(tmp_file)

    logger.info(
        f"Saving {bucket}:{key} to the database and to the Zarr "
        f"store at: {zarr_upload}"
    )
    engine = create_engine(os.environ["FLASK_SQLALCHEMY_DATABASE_URI"])
    with Session(engine) as session:
        diag.save(session, zarr_upload, parquet_upload, data)
    engine.dispose()

    logger.info(f"Done processing {bucket}:{key}")
