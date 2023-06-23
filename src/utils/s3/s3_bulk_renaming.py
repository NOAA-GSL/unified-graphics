import argparse
import re
from typing import Optional

import boto3  # type: ignore


def list_objects(bucket_name: str, prefix: Optional[str] = None) -> list[str]:
    """
    Lists all objects in the specified S3 bucket matching the given prefix.
    Returns a list of object keys.
    """
    s3 = boto3.client("s3")
    keys: list[str] = []

    paginator = s3.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    for page in page_iterator:
        if "Contents" in page:
            keys.extend(obj["Key"] for obj in page["Contents"])
    return keys


def filter_objects(object_keys: list[str]) -> list[str]:
    """
    Filters the list of object keys based on the provided regex pattern.
    Returns a list of filtered object keys.
    """
    return [key for key in object_keys if detect_timestamps_without_minutes(key)]


def detect_timestamps_without_minutes(key: str) -> Optional[str]:
    """
    Returns the string if it contains a YYYY-MM-DDTHH timestamp.
    Otherwise, return None
    """
    pattern_with_minutes = r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})"  # "YYYY-MM-DDTHH:MM"
    pattern_without_minutes = r"(\d{4}-\d{2}-\d{2}T\d{2})"  # "YYYY-MM-DDTHH"

    match_with_minutes = re.search(pattern_with_minutes, key)
    match_without_minutes = re.search(pattern_without_minutes, key)

    return key if match_without_minutes and not match_with_minutes else None


def update_timestamp(string) -> str:
    """Updates YYYY-MM-DDTHH timestamps with a :MM field set to the start of the hour"""
    desired_format = r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})"  # "YYYY-MM-DDTHH:MM"
    if re.search(desired_format, string):
        return string
    return re.sub(r"(^.*\d{4}-\d{2}-\d{2}T\d{2})(.*$)", r"\1:00\2", string)


def rename_objects(bucket_name: str, object_keys: list[str]) -> None:
    """
    Renames the objects in the specified S3 bucket by adding ":00" to the object key.
    """
    s3 = boto3.client("s3")

    for key in object_keys:
        new_key = update_timestamp(key)

        print(f"Copying: {key} to {new_key}")
        s3.copy_object(
            Bucket=bucket_name,
            CopySource={"Bucket": bucket_name, "Key": key},
            Key=new_key,
        )

        print(f"Removing old key: {key}")
        s3.delete_object(Bucket=bucket_name, Key=key)

        print(f"Renamed object: {key} to {new_key}")


def process_objects(bucket_name: str, prefix: str, dry_run: bool) -> None:
    """
    Process objects in the specified S3 bucket by listing, filtering, and renaming them.
    """
    # List all objects in the bucket
    object_keys = list_objects(bucket_name, prefix)
    print(f"Number of keys found in the bucket: {len(object_keys)}")

    # Filter the objects based on regex pattern
    filtered_keys = filter_objects(object_keys)
    print("Filtered keys are: ")
    print(filtered_keys)
    print(f"Number of keys without minutes: {len(filtered_keys)}")

    # Rename the filtered objects
    if not dry_run:
        rename_objects(bucket_name, filtered_keys)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bucket",
        type=str,
        required=True,
        help="The S3 bucket name like: my-s3-bucket",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        required=False,
        help="The S3 bucket prefix to rename like: diagnostics.zarr",
    )
    parser.add_argument(
        "--dry-run",
        default=True,
        required=False,
        help="Do a dry run - everything up to renaming objects in the S3 bucket",
        action=argparse.BooleanOptionalAction,
    )
    args = parser.parse_args()

    if args.dry_run:
        print(
            "Dry run - Objects won't be renamed in S3. \n\n"
            "Use --no-dry-run once you've confirmed the results are as desired.\n"
        )

    process_objects(args.bucket, args.prefix, args.dry_run)
