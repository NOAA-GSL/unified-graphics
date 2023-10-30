import uuid
from functools import partial

import numpy as np
import pandas as pd
import pytest
import xarray as xr
from botocore.session import Session
from moto.server import ThreadedMotoServer
from s3fs import S3FileSystem, S3Map
from werkzeug.datastructures import MultiDict

from unified_graphics import diag
from unified_graphics.models import Analysis, WeatherModel

# Global resources for s3
test_bucket_name = "osti-modeling-dev-rtma-vis"


@pytest.fixture
def aws_credentials(monkeypatch):
    credentials = {
        "AWS_ACCESS_KEY_ID": "test-id",
        "AWS_SECRET_ACCESS_KEY": "test-key",
        "AWS_SECURITY_TOKEN": "test-token",
        "AWS_SESSION_TOKEN": "test-session",
        "AWS_DEFAULT_REGION": "us-east-1",
    }

    for k, v in credentials.items():
        monkeypatch.setenv(k, v)

    return credentials


@pytest.fixture(scope="module")
def moto_server():
    server = ThreadedMotoServer(port=9000)
    server.start()
    yield "http://127.0.0.1:9000"
    server.stop()


@pytest.fixture
def s3_client(aws_credentials, moto_server):
    session = Session()
    return session.create_client("s3", endpoint_url=moto_server)


@pytest.fixture
def test_key_prefix():
    return f"/test/{uuid.uuid4()}/"


def test_get_model_metadata(session):
    model_run_list = [
        ("RTMA", "WCOSS", "CONUS", "REALTIME", "HRRR", "2023-03-17T14:00"),
        ("3DRTMA", "JET", "CONUS", "RETRO", "RRFS", "2023-03-17T15:00"),
    ]

    variable_list = ["ps", "q", "t", "uv"]

    for model, system, domain, freq, bg, init_time in model_run_list:
        wx_model = WeatherModel(name=model, background=WeatherModel(name=bg))
        analysis = Analysis(
            time=init_time,
            domain=domain,
            frequency=freq,
            system=system,
            model=wx_model,
        )
        session.add(analysis)

    result = diag.get_model_metadata(session)

    assert result == diag.ModelMetadata(
        model_list=["3DRTMA", "RTMA"],
        system_list=["JET", "WCOSS"],
        domain_list=["CONUS"],
        frequency_list=["REALTIME", "RETRO"],
        background_list=["HRRR", "RRFS"],
        init_time_list=["2023-03-17T14:00", "2023-03-17T15:00"],
        variable_list=variable_list,
    )


@pytest.mark.parametrize(
    "uri,expected",
    [
        ("file:///tmp/diag.zarr", "/tmp/diag.zarr"),
        ("/tmp/diag.zarr", "/tmp/diag.zarr"),
    ],
)
def test_get_store_file(uri, expected):
    result = diag.get_store(uri)

    assert result == expected


def test_get_store_s3(moto_server, s3_client, monkeypatch):
    client = {"region_name": "us-east-1"}
    uri = "s3://bucket/prefix/diag.zarr"
    s3_client.create_bucket(Bucket="bucket")
    s3_client.put_object(Bucket="bucket", Body=b"Test object", Key="prefix/diag.zarr")

    monkeypatch.setattr(
        diag,
        "S3FileSystem",
        partial(diag.S3FileSystem, endpoint_url=moto_server),
    )

    result = diag.get_store(uri)

    assert result == S3Map(
        root=uri,
        s3=S3FileSystem(
            client_kwargs=client,
            endpoint_url=moto_server,
        ),
        check=False,
    )


def test_open_diagnostic(tmp_path, test_dataset):
    diag_zarr_file = str(tmp_path / "test_diag.zarr")
    expected = test_dataset()
    group = "/".join(
        (
            expected.model,
            expected.system,
            expected.domain,
            expected.background,
            expected.frequency,
            expected.name,
            expected.initialization_time,
            expected.loop,
        )
    )

    expected.to_zarr(diag_zarr_file, group=group, consolidated=False)

    result = diag.open_diagnostic(
        diag_zarr_file,
        expected.model,
        expected.system,
        expected.domain,
        expected.background,
        expected.frequency,
        diag.Variable(expected.name),
        expected.initialization_time,
        diag.MinimLoop(expected.loop),
    )

    xr.testing.assert_equal(result, expected)


@pytest.mark.parametrize(
    "uri,expected",
    [
        (
            "foo://an/unknown/uri.zarr",
            "Unsupported protocol 'foo' for URI: 'foo://an/unknown/uri.zarr'",
        ),
        (
            "ftp://an/unsupported/uri.zarr",
            "Unsupported protocol 'ftp' for URI: 'ftp://an/unsupported/uri.zarr'",
        ),
    ],
)
def test_open_diagnostic_unknown_uri(uri, expected):
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    background = "HRRR"
    frequency = "REALTIME"
    init_time = "2022-05-16T04:00"

    with pytest.raises(ValueError, match=expected):
        diag.open_diagnostic(
            uri,
            model,
            system,
            domain,
            background,
            frequency,
            init_time,
            diag.Variable.WIND,
            diag.MinimLoop.GUESS,
        )


@pytest.mark.usefixtures("aws_credentials")
def test_open_diagnostic_s3(moto_server, test_dataset, monkeypatch):
    store = "s3://test_open_diagnostic_s3/test_diag.zarr"
    expected = test_dataset()
    group = "/".join(
        (
            expected.model,
            expected.system,
            expected.domain,
            expected.background,
            expected.frequency,
            expected.name,
            expected.initialization_time,
            expected.loop,
        )
    )

    monkeypatch.setattr(
        diag,
        "S3FileSystem",
        partial(diag.S3FileSystem, endpoint_url=moto_server),
    )

    expected.to_zarr(
        store,
        group=group,
        consolidated=False,
        storage_options={"endpoint_url": moto_server},
    )

    result = diag.open_diagnostic(
        store,
        expected.model,
        expected.system,
        expected.domain,
        expected.background,
        expected.frequency,
        diag.Variable(expected.name),
        expected.initialization_time,
        diag.MinimLoop(expected.loop),
    )

    xr.testing.assert_equal(result, expected)


# Test cases taken from the examples at
# http://ncl.ucar.edu/Document/Functions/Contributed/wind_direction.shtml
@pytest.mark.parametrize(
    "u,v,expected",
    (
        [
            np.array([10, 0, 0, -10, 10, 10, -10, -10]),
            np.array([0, 10, -10, 0, 10, -10, 10, -10]),
            np.array([270, 180, 0, 90, 225, 315, 135, 45]),
        ],
        [
            np.array([0.0, -0.0, 0.0, -0.0]),
            np.array([0.0, 0.0, -0.0, -0.0]),
            np.array([0.0, 0.0, 0.0, 0.0]),
        ],
    ),
)
def test_vector_direction(u, v, expected):
    result = diag.vector_direction(u, v)

    np.testing.assert_array_almost_equal(result, expected, decimal=5)


def test_vector_magnitude():
    u = np.array([1, 0, 1, 0])
    v = np.array([0, 1, 1, 0])

    result = diag.vector_magnitude(u, v)

    np.testing.assert_array_almost_equal(
        result, np.array([1, 1, 1.41421, 0]), decimal=5
    )


@pytest.mark.parametrize(
    "mapping,expected",
    [
        ([("a", "1")], [("a", np.array([1.0]), np.array([1.0]))]),
        ([("a", "1::2")], [("a", np.array([1.0]), np.array([2.0]))]),
        ([("a", "2,4::3,1")], [("a", np.array([2.0, 1.0]), np.array([3.0, 4.0]))]),
    ],
    scope="class",
)
class TestGetBounds:
    @pytest.fixture(scope="class")
    def result(self, mapping):
        filters = MultiDict(mapping)
        return list(diag.get_bounds(filters))

    def test_coord(self, result, expected):
        assert result[0][0] == expected[0][0]

    def test_lower_bounds(self, result, expected):
        assert (result[0][1] == expected[0][1]).all()

    def test_upper_bounds(self, result, expected):
        assert (result[0][2] == expected[0][2]).all()


def test_history(tmp_path, test_dataset, diag_parquet):
    run_list = [
        {
            "initialization_time": "2022-05-16T04:00",
            "observation": [10, 20],
            "forecast_unadjusted": [5, 10],
            "is_used": [True, True],
            # O - F [5, 10]
        },
        {
            "initialization_time": "2022-05-16T07:00",
            "observation": [1, 2, 3],
            "forecast_unadjusted": [5, 10, 3],
            "longitude": [0, 0, 0],
            "latitude": [0, 0, 0],
            "is_used": [True, True, True],
            # O - F [-4, -8, 0]
        },
    ]

    for run in run_list:
        data = test_dataset(
            model="RTMA",
            system="WCOSS",
            domain="CONUS",
            background="RRFS",
            frequency="REALTIME",
            variable="ps",
            loop="ges",
            **run,
        )
        diag_parquet(data)

    result = diag.history(
        f"file://{tmp_path}/",
        "RTMA",
        "WCOSS",
        "CONUS",
        "RRFS",
        "REALTIME",
        diag.Variable.PRESSURE,
        diag.MinimLoop.GUESS,
        MultiDict(),
    )

    pd.testing.assert_frame_equal(
        result,
        pd.DataFrame(
            {
                "initialization_time": ["2022-05-16T04:00", "2022-05-16T07:00"],
                "min": [5.0, -8.0],
                "max": [10.0, 0.0],
                "mean": [7.5, -4.0],
                "count": [2.0, 3.0],
            }
        ),
    )


def test_history_s3(aws_credentials, moto_server, s3_client, test_dataset, monkeypatch):
    bucket = "test_history_s3"
    store = f"s3://{bucket}/"
    s3_client.create_bucket(Bucket=bucket)

    storage_options = {"client_kwargs": {"endpoint_url": moto_server}}
    monkeypatch.setattr(
        diag.pd,
        "read_parquet",
        partial(pd.read_parquet, storage_options=storage_options),
    )

    run_list = [
        {
            "initialization_time": "2022-05-16T04:00",
            "observation": [10, 20],
            "forecast_unadjusted": [5, 10],
            "is_used": [True, True],
            # O - F [5, 10]
        },
        {
            "initialization_time": "2022-05-16T07:00",
            "observation": [1, 2, 3],
            "forecast_unadjusted": [5, 10, 3],
            "longitude": [0, 0, 0],
            "latitude": [0, 0, 0],
            "is_used": [True, True, True],
            # O - F [-4, -8, 0]
        },
    ]

    for run in run_list:
        data = test_dataset(
            model="RTMA",
            system="WCOSS",
            domain="CONUS",
            background="RRFS",
            frequency="REALTIME",
            variable="ps",
            loop="ges",
            **run,
        ).to_dataframe()
        data["loop"] = "ges"
        data["initialization_time"] = run["initialization_time"]

        data.to_parquet(
            f"s3://{bucket}/RTMA_RRFS_WCOSS_CONUS_REALTIME/ps",
            partition_cols=["loop"],
            index=True,
            engine="pyarrow",
            storage_options=storage_options,
        )

    result = diag.history(
        store,
        "RTMA",
        "WCOSS",
        "CONUS",
        "RRFS",
        "REALTIME",
        diag.Variable.PRESSURE,
        diag.MinimLoop.GUESS,
        MultiDict(),
    )

    pd.testing.assert_frame_equal(
        result,
        pd.DataFrame(
            {
                "initialization_time": ["2022-05-16T04:00", "2022-05-16T07:00"],
                "min": [5.0, -8.0],
                "max": [10.0, 0.0],
                "mean": [7.5, -4.0],
                "count": [2.0, 3.0],
            }
        ),
    )
