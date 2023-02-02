from pathlib import Path
from unittest import mock

import pytest
from ugdata import aws


@mock.patch("ugdata.aws.open")
@mock.patch("gzip.open")
@mock.patch("shutil.copyfileobj")
@mock.patch("ugdata.aws.s3_client", autospec=True)
@mock.patch("uuid.uuid4")
@pytest.mark.parametrize(
    "key,expected_download,expected_path",
    [
        (
            "diag_t_anl.202301300600.nc4.gz",
            "/tmp/mock-uuid-diag_t_anl.202301300600.nc4.gz",
            "/tmp/mock-uuid-diag_t_anl.202301300600.nc4",
        ),
        (
            "ncdiag_conv_t_anl.nc4.2023013006",
            "/tmp/mock-uuid-ncdiag_conv_t_anl.nc4.2023013006",
            "/tmp/mock-uuid-ncdiag_conv_t_anl.nc4.2023013006",
        ),
    ],
)
def test_fetch_record(
    mock_uuid4,
    mock_s3_client,
    mock_copyfileobj,
    mock_gzip_open,
    mock_open,
    key,
    expected_download,
    expected_path,
):
    bucket = "s3://test-bucket"
    mock_uuid4.return_value = "mock-uuid"

    result = aws.fetch_record(bucket, key)

    mock_s3_client.download_file.assert_called_once_with(bucket, key, expected_download)
    assert result == Path(expected_path)


@mock.patch("ugdata.diag.save")
@mock.patch("ugdata.diag.load")
@mock.patch("ugdata.aws.fetch_record")
def test_handler(mock_fetch_record, mock_load, mock_save, monkeypatch):
    ug_bucket = "s3://test-bucket/test.zarr"
    dl_bucket = "s3://test-diag-bucket"
    key = "diag_t_anl.202301300600.nc4.gz"

    monkeypatch.setenv("UG_DIAG_ZARR", ug_bucket)

    context = {}
    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": dl_bucket,
                    },
                    "object": {
                        "key": key,
                    },
                }
            }
        ]
    }

    aws.lambda_handler(event, context)

    mock_fetch_record.assert_called_once_with(dl_bucket, key)
    mock_load.assert_called_once_with(mock_fetch_record.return_value)
    mock_save.assert_called_once_with(ug_bucket, mock_load.return_value)
