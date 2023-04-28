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
    "key,expected_download,expected_path,prefix_to_strip",
    [
        (
            "diag_t_anl.202301300600.nc4.gz",
            "/tmp/mock-uuid-diag_t_anl.202301300600.nc4.gz",
            "/tmp/mock-uuid-diag_t_anl.202301300600.nc4",
            None,
        ),
        (
            "ncdiag_conv_t_anl.nc4.2023013006",
            "/tmp/mock-uuid-ncdiag_conv_t_anl.nc4.2023013006",
            "/tmp/mock-uuid-ncdiag_conv_t_anl.nc4.2023013006",
            None,
        ),
        (
            "RTMA/foo/ncdiag_conv_t_anl.nc4.2023013006",
            "/tmp/mock-uuid-RTMA_foo_ncdiag_conv_t_anl.nc4.2023013006",
            "/tmp/mock-uuid-RTMA_foo_ncdiag_conv_t_anl.nc4.2023013006",
            "diag",
        ),
        (
            "diag/RTMA/foo/ncdiag_conv_t_anl.nc4.2023013006",
            "/tmp/mock-uuid-RTMA_foo_ncdiag_conv_t_anl.nc4.2023013006",
            "/tmp/mock-uuid-RTMA_foo_ncdiag_conv_t_anl.nc4.2023013006",
            "diag",
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
    prefix_to_strip,
    monkeypatch,
):
    bucket = "s3://test-bucket"
    mock_uuid4.return_value = "mock-uuid"
    if prefix_to_strip:
        monkeypatch.setenv("UG_DIAG_KEY_PREFIX", prefix_to_strip)

    result = aws.fetch_record(bucket, key)

    mock_s3_client.download_file.assert_called_once_with(bucket, key, expected_download)
    assert result == Path(expected_path)


def test_handler_test_event():
    context = {}
    event = {"Event": "s3:TestEvent"}

    result = aws.lambda_handler(event, context)

    assert result == "Test event received"


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
        "detail": {
            "bucket": {"name": dl_bucket},
            "object": {"key": key},
        }
    }

    aws.lambda_handler(event, context)

    mock_fetch_record.assert_called_once_with(dl_bucket, key)
    mock_load.assert_called_once_with(mock_fetch_record.return_value)
    mock_save.assert_called_once_with(ug_bucket, mock_load.return_value)


def test_handler_no_records(monkeypatch):
    context = {}
    event = {}
    ug_bucket = "s3://test-bucket/test.zarr"
    monkeypatch.setenv("UG_DIAG_ZARR", ug_bucket)

    result = aws.lambda_handler(event, context)

    assert result == ""


@mock.patch("ugdata.diag.save")
@mock.patch("ugdata.diag.load")
@mock.patch("ugdata.aws.fetch_record")
def test_handler_skip_second_loop(mock_fetch_record, mock_load, mock_save, monkeypatch):
    ug_bucket = "s3://test-bucket/test.zarr"
    dl_bucket = "s3://test-diag-bucket"
    key = "diag_t_02.202301300600.nc4.gz"

    monkeypatch.setenv("UG_DIAG_ZARR", ug_bucket)

    context = {}
    event = {
        "detail": {
            "bucket": {"name": dl_bucket},
            "object": {"key": key},
        }
    }

    aws.lambda_handler(event, context)

    mock_fetch_record.assert_not_called()
    mock_load.assert_not_called()
    mock_save.assert_not_called()
