from datetime import datetime
from functools import partial

import numpy as np
import pandas as pd
import pytest
from botocore.session import Session
from moto.server import ThreadedMotoServer
from werkzeug.datastructures import MultiDict

from unified_graphics import diag
from unified_graphics.models import Analysis, WeatherModel


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


def test_history(tmp_path, test_dataset, diag_parquet):
    run_list = [
        {
            "initialization_time": datetime.fromisoformat("2022-05-16T04:00"),
            "observation": [10, 14, 18, 20],
            "forecast_unadjusted": [5, 7, 10, 10],
            "longitude": [0, 0, 0, 0],
            "latitude": [0, 0, 0, 0],
            "is_used": [True, True, True, True],
            # O - F [5, 7, 8, 10]
        },
        {
            "initialization_time": datetime.fromisoformat("2022-05-16T07:00"),
            "observation": [1, 2, 3, 4, 5],
            "forecast_unadjusted": [3, 5, 6, 7, 10],
            "longitude": [0, 0, 0, 0, 0],
            "latitude": [0, 0, 0, 0, 0],
            "is_used": [True, True, True, True, True],
            # O - F [-2, -3, -3, -3, -5]
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
        run_list[1]["initialization_time"],
        MultiDict(),
    )

    pd.testing.assert_frame_equal(
        result,
        pd.DataFrame(
            {
                "initialization_time": np.array(
                    [r["initialization_time"] for r in run_list], dtype="datetime64[us]"
                ),
                "min": [5.0, -5.0],
                "25%": [6.5, -3.0],
                "50%": [7.5, -3.0],
                "75%": [8.5, -3.0],
                "max": [10.0, -2.0],
                "mean": [7.5, -3.2],
                "count": [4.0, 5.0],
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
            "initialization_time": datetime.fromisoformat("2022-05-16T04:00"),
            "observation": [10, 14, 18, 20],
            "forecast_unadjusted": [5, 7, 10, 10],
            "longitude": [0, 0, 0, 0],
            "latitude": [0, 0, 0, 0],
            "is_used": [True, True, True, True],
            # O - F [5, 7, 8, 10]
        },
        {
            "initialization_time": datetime.fromisoformat("2022-05-16T07:00"),
            "observation": [1, 2, 3, 4, 5],
            "forecast_unadjusted": [3, 5, 6, 7, 10],
            "longitude": [0, 0, 0, 0, 0],
            "latitude": [0, 0, 0, 0, 0],
            "is_used": [True, True, True, True, True],
            # O - F [-2, -3, -3, -3, -5]
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
        run_list[0]["initialization_time"],
        MultiDict(),
    )

    pd.testing.assert_frame_equal(
        result,
        pd.DataFrame(
            {
                "initialization_time": np.array(
                    ["2022-05-16T04:00"], dtype="datetime64[us]"
                ),
                "min": [5.0],
                "25%": [6.5],
                "50%": [7.5],
                "75%": [8.5],
                "max": [10.0],
                "mean": [7.5],
                "count": [4.0],
            }
        ),
    )
