from unittest import mock

import pytest

from utils.s3.s3_bulk_renaming import (
    detect_timestamps_without_minutes,
    filter_objects,
    list_objects,
    rename_objects,
    update_timestamp,
)


@pytest.fixture
def sample_objects():
    return [
        {"Key": "file1.txt"},
        {"Key": "file2.jpg"},
        {"Key": "file3.txt"},
        {"Key": "file4.txt"},
        {
            "Key": (
                "diagnostics.zarr/RTMA/WCOSS/CONUS/RRFS/REALTIME/uv/"
                "2023-06-06T16/ges/observation/1.1"
            )
        },
        {
            "Key": (
                "diagnostics.zarr/RTMA/WCOSS/CONUS/RRFS/REALTIME/uv/"
                "2023-06-06T16:00/ges/observation/1.1"
            )
        },
    ]


class TestDetectTimestamps:
    def test_without_minutes(self):
        key = (
            "diagnostics.zarr/RTMA/WCOSS/CONUS/RRFS/REALTIME/uv/"
            "2023-06-06T16/ges/observation/1.1"
        )

        assert key == detect_timestamps_without_minutes(key)

    def test_with_minutes(self):
        key = (
            "diagnostics.zarr/RTMA/WCOSS/CONUS/RRFS/REALTIME/uv/"
            "2023-06-06T16:00/ges/observation/1.1"
        )

        assert detect_timestamps_without_minutes(key) is None

    def test_no_timestamp(self):
        key = "foo/bar/baz"

        assert detect_timestamps_without_minutes(key) is None


class TestUpdateTimestamp:
    def test_update_timestamp(self):
        key = (
            "diagnostics.zarr/RTMA/WCOSS/CONUS/RRFS/REALTIME/uv/"
            "2023-06-06T16/ges/observation/1.1"
        )
        desired = (
            "diagnostics.zarr/RTMA/WCOSS/CONUS/RRFS/REALTIME/uv/"
            "2023-06-06T16:00/ges/observation/1.1"
        )

        assert desired == update_timestamp(key)

    def test_simplified_timestamp(self):
        key = "foo/2023-06-06T16/bar"
        desired = "foo/2023-06-06T16:00/bar"

        assert desired == update_timestamp(key)

    def test_bare_timestamp(self):
        key = "2023-06-06T16"
        desired = "2023-06-06T16:00"

        assert desired == update_timestamp(key)

    def test_matching_timestamps(self):
        key = "2023-06-06T16:00"
        desired = "2023-06-06T16:00"

        assert desired == update_timestamp(key)

    def test_no_timestamp(self):
        key = "foo/bar"
        desired = "foo/bar"

        assert desired == update_timestamp(key)


@mock.patch("utils.s3.s3_bulk_renaming.boto3.client")
def test_list_bucket_objects(mock_client, sample_objects):
    # Convert sample_objects to a list of values
    expected_objects = [obj["Key"] for obj in sample_objects]

    # Test config
    bucket_name = "a-bucket"
    prefix = "a/prefix"

    # Mock the s3 client, paginator, and page_iterator
    mock_s3_client = mock_client.return_value
    mock_paginator = mock_s3_client.get_paginator.return_value
    mock_page_iterator = mock_paginator.paginate.return_value

    # Add pages to the paginator
    mock_pages = [{"Contents": sample_objects[:3]}, {"Contents": sample_objects[3:]}]
    mock_page_iterator.__iter__.return_value = mock_pages

    # Run the method we're testing
    objects = list_objects(bucket_name, prefix)

    mock_paginator.paginate.assert_called_once_with(Bucket=bucket_name, Prefix=prefix)
    assert objects == expected_objects


def test_filter_objects(sample_objects):
    # Convert sample_objects to a list of values
    objs = [obj["Key"] for obj in sample_objects]
    expected_filtered_objects = [
        (
            "diagnostics.zarr/RTMA/WCOSS/CONUS/RRFS/REALTIME/uv/"
            "2023-06-06T16/ges/observation/1.1"
        )
    ]

    filtered_objects = filter_objects(objs)

    assert filtered_objects == expected_filtered_objects


@mock.patch("utils.s3.s3_bulk_renaming.boto3.client")
def test_rename_objects(mock_client, sample_objects):
    mock_s3_client = mock_client.return_value

    # Convert sample_objects to a list of values
    objs = [obj["Key"] for obj in sample_objects]
    rename_objects("your-bucket-name", objs)

    mock_s3_client.copy_object.assert_called()
    mock_s3_client.delete_object.assert_called()
