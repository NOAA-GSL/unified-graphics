"""Test saving xarray Datasets to Zarr"""

from datetime import datetime

import pandas as pd
import pytest
import xarray as xr
from sqlalchemy import func, select

from unified_graphics.etl import diag
from unified_graphics.models import Analysis, WeatherModel


@pytest.fixture(scope="module")
def model():
    mdl = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    frequency = "REALTIME"
    background = "HRRR"

    return (mdl, system, domain, background, frequency)


@pytest.fixture(scope="class")
def data_path(tmp_path_factory):
    return tmp_path_factory.mktemp("test_etl_save")


@pytest.fixture(scope="class")
def zarr_file(data_path):
    return data_path / "unified_graphics.zarr"


@pytest.fixture(scope="class")
def parquet_file(model, data_path):
    (mdl, system, domain, background, frequency) = model
    return data_path / "_".join((mdl, background, system, domain, frequency))


def dataset_to_table(dataset: xr.Dataset) -> pd.DataFrame:
    df = dataset.to_dataframe()
    df["observation_class"] = dataset.name
    df["loop"] = dataset.loop
    df = df.astype({"observation_class": "category", "loop": "category"})

    return df


class TestSaveNew:
    @pytest.fixture(scope="class", autouse=True)
    def dataset(self, model, diag_dataset, session, zarr_file):
        (mdl, system, domain, background, frequency) = model
        ps = diag_dataset(
            "ps",
            "2022-05-05T14:00",
            "anl",
            mdl,
            system,
            domain,
            frequency,
            background,
        )

        diag.save(session, zarr_file, ps)

        return ps

    @pytest.fixture(scope="class")
    def dataframe(self, dataset):
        return dataset_to_table(dataset)

    def test_zarr_created(self, model, dataset, zarr_file):
        group = "/".join((*model, "ps", "2022-05-05T14:00", "anl"))
        result = xr.open_zarr(zarr_file, group=group, consolidated=False)

        xr.testing.assert_equal(result, dataset)

    def test_parquet_created(self, dataframe, parquet_file):
        result = pd.read_parquet(
            parquet_file,
            filters=(("observation_class", "=", "ps"), ("loop", "=", "anl")),
        )

        pd.testing.assert_frame_equal(result, dataframe)

    def test_analysis_created(self, model, session):
        (mdl, system, domain, background, frequency) = model
        bg_model = session.scalar(
            select(WeatherModel).where(WeatherModel.name == background)
        )
        wx_model = session.scalar(
            select(WeatherModel).where(
                WeatherModel.name == mdl, WeatherModel.background_id == bg_model.id
            )
        )
        analysis_count = session.scalar(
            select(func.count())
            .select_from(Analysis)
            .where(
                Analysis.time == datetime.fromisoformat("2022-05-05T14:00"),
                Analysis.domain == domain,
                Analysis.frequency == frequency,
                Analysis.system == system,
                Analysis.model_id == wx_model.id,
            )
        )

        assert analysis_count == 1


class TestAddVariable:
    @pytest.fixture(scope="class", autouse=True)
    def dataset(self, model, diag_dataset, session, zarr_file):
        (mdl, system, domain, background, frequency) = model
        ps = diag_dataset(
            "ps",
            "2022-05-05T14:00",
            "anl",
            mdl,
            system,
            domain,
            frequency,
            background,
        )

        diag.save(session, zarr_file, ps)

        t = diag_dataset(
            "t",
            "2022-05-05T14:00",
            "anl",
            mdl,
            system,
            domain,
            frequency,
            background,
        )

        diag.save(session, zarr_file, t)

        return (ps, t)

    @pytest.fixture(scope="class")
    def dataframe(self, dataset):
        return tuple(
            df.astype(
                {
                    "observation_class": pd.CategoricalDtype(
                        categories=["ps", "t"], ordered=False
                    )
                }
            )
            for df in map(dataset_to_table, dataset)
        )

    @pytest.mark.parametrize("variable,expected", (("ps", 0), ("t", 1)))
    def test_zarr(self, dataset, model, zarr_file, variable, expected):
        group = "/".join((*model, variable, "2022-05-05T14:00", "anl"))
        result = xr.open_zarr(zarr_file, group=group, consolidated=False)
        xr.testing.assert_equal(result, dataset[expected])

    @pytest.mark.parametrize("variable,expected", (("ps", 0), ("t", 1)))
    def test_parquet(self, dataframe, parquet_file, variable, expected):
        result = pd.read_parquet(
            parquet_file,
            filters=(("observation_class", "=", variable), ("loop", "=", "anl")),
        )

        pd.testing.assert_frame_equal(result, dataframe[expected])

    def test_analysis_metadata(self, session):
        analysis_count = session.scalar(select(func.count()).select_from(Analysis))
        assert analysis_count == 1


class TestAddLoop:
    @pytest.fixture(scope="class", autouse=True)
    def dataset(self, model, diag_dataset, session, zarr_file):
        (mdl, system, domain, background, frequency) = model
        ges = diag_dataset(
            "ps",
            "2022-05-05T14:00",
            "ges",
            mdl,
            system,
            domain,
            frequency,
            background,
        )

        diag.save(session, zarr_file, ges)

        anl = diag_dataset(
            "ps",
            "2022-05-05T14:00",
            "anl",
            mdl,
            system,
            domain,
            frequency,
            background,
        )

        diag.save(session, zarr_file, anl)

        return (ges, anl)

    @pytest.fixture(scope="class")
    def dataframe(self, dataset):
        return tuple(
            df.astype(
                {"loop": pd.CategoricalDtype(categories=["anl", "ges"], ordered=False)}
            )
            for df in map(dataset_to_table, dataset)
        )

    @pytest.mark.parametrize("loop,expected", (("ges", 0), ("anl", 1)))
    def test_zarr(self, dataset, model, zarr_file, loop, expected):
        group = "/".join((*model, "ps", "2022-05-05T14:00", loop))
        result = xr.open_zarr(zarr_file, group=group, consolidated=False)
        xr.testing.assert_equal(result, dataset[expected])

    @pytest.mark.parametrize("loop,expected", (("ges", 0), ("anl", 1)))
    def test_parquet(self, dataframe, parquet_file, loop, expected):
        result = pd.read_parquet(
            parquet_file,
            filters=(("observation_class", "=", "ps"), ("loop", "=", loop)),
        )

        pd.testing.assert_frame_equal(result, dataframe[expected])

    def test_analysis_metadata(self, session):
        analysis_count = session.scalar(select(func.count()).select_from(Analysis))
        assert analysis_count == 1


class TestAddAnalysis:
    @pytest.fixture(scope="class", autouse=True)
    def dataset(self, model, diag_dataset, session, zarr_file):
        (mdl, system, domain, background, frequency) = model
        first = diag_dataset(
            "ps",
            "2022-05-05T14:00",
            "ges",
            mdl,
            system,
            domain,
            frequency,
            background,
        )

        diag.save(session, zarr_file, first)

        second = diag_dataset(
            "ps",
            "2022-05-05T15:00",
            "ges",
            mdl,
            system,
            domain,
            frequency,
            background,
        )

        diag.save(session, zarr_file, second)

        return (first, second)

    @pytest.fixture(scope="class")
    def dataframe(self, dataset):
        return pd.concat(map(dataset_to_table, dataset))

    @pytest.mark.parametrize(
        "init_time,expected", (("2022-05-05T14:00", 0), ("2022-05-05T15:00", 1))
    )
    def test_zarr(self, dataset, model, zarr_file, init_time, expected):
        group = "/".join((*model, "ps", init_time, "ges"))
        result = xr.open_zarr(zarr_file, group=group, consolidated=False)
        xr.testing.assert_equal(result, dataset[expected])

    def test_parquet(self, dataframe, parquet_file):
        result = pd.read_parquet(
            parquet_file,
            filters=(("observation_class", "=", "ps"), ("loop", "=", "ges")),
        )

        pd.testing.assert_frame_equal(result, dataframe)

    def test_analysis_metadata(self, session):
        analysis_count = session.scalar(select(func.count()).select_from(Analysis))
        assert analysis_count == 2
