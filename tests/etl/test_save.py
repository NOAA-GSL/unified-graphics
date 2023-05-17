"""Test saving xarray Datasets to Zarr"""

from datetime import datetime

import pytest
import xarray as xr
from sqlalchemy import func, select

from unified_graphics.etl import diag
from unified_graphics.models import Analysis, WeatherModel


@pytest.fixture
def zarr_file(tmp_path):
    return tmp_path / "unified_graphics.zarr"


@pytest.fixture(scope="module")
def analysis():
    init_time = "2022-05-05T14"
    model = "RTMA"
    system = "WCOSS"
    domain = "CONUS"
    frequency = "REALTIME"
    background = "HRRR"

    return (init_time, model, system, domain, frequency, background)


@pytest.fixture
def ps_anl(analysis, diag_dataset, session, zarr_file):
    (init_time, model, system, domain, frequency, background) = analysis
    ps = diag_dataset(
        "ps", init_time, "anl", model, system, domain, frequency, background
    )

    diag.save(session, zarr_file, ps)

    return ps


@pytest.fixture
def ps_ges(analysis, diag_dataset, session, zarr_file):
    (init_time, model, system, domain, frequency, background) = analysis
    ps = diag_dataset(
        "ps", init_time, "ges", model, system, domain, frequency, background
    )

    diag.save(session, zarr_file, ps)

    return ps


@pytest.fixture
def t_anl(analysis, diag_dataset, session, zarr_file):
    (init_time, model, system, domain, frequency, background) = analysis
    t = diag_dataset(
        "t", init_time, "anl", model, system, domain, frequency, background
    )

    diag.save(session, zarr_file, t)

    return t


def test_save_new(ps_anl, analysis, zarr_file, session):
    """diag.save should create a new Zarr on first write"""
    (init_time, model, system, domain, frequency, background) = analysis

    xr.testing.assert_equal(
        xr.open_zarr(
            zarr_file,
            group=(
                f"{model}/{system}/{domain}/{background}/{frequency}/"
                f"ps/{init_time}/anl"
            ),
        ),
        ps_anl,
    )

    bg_model = session.scalar(
        select(WeatherModel).where(WeatherModel.name == background)
    )
    assert bg_model, "Background model not created"

    wx_model = session.scalar(
        select(WeatherModel).where(
            WeatherModel.name == model, WeatherModel.background_id == bg_model.id
        )
    )
    assert wx_model, "Model not created in database"

    analysis_count = session.scalar(
        select(func.count())
        .select_from(Analysis)
        .where(
            Analysis.time == datetime.fromisoformat(init_time),
            Analysis.domain == domain,
            Analysis.frequency == frequency,
            Analysis.system == system,
            Analysis.model_id == wx_model.id,
        )
    )
    assert analysis_count == 1, "Analysis row not created in database"


def test_add_loop(ps_anl, ps_ges, analysis, zarr_file, session):
    """diag.save should add a new group for each loop"""

    (init_time, model, system, domain, frequency, background) = analysis

    xr.testing.assert_equal(
        xr.open_zarr(
            zarr_file,
            group=(
                f"{model}/{system}/{domain}/{background}/{frequency}/"
                f"ps/{init_time}/anl"
            ),
        ),
        ps_anl,
    )

    xr.testing.assert_equal(
        xr.open_zarr(
            zarr_file,
            group=(
                f"{model}/{system}/{domain}/{background}/{frequency}/"
                f"ps/{init_time}/ges"
            ),
        ),
        ps_ges,
    )

    analysis_count = session.scalar(select(func.count()).select_from(Analysis))
    assert analysis_count == 1


def test_add_variable(ps_anl, t_anl, analysis, zarr_file, session):
    """diag.save should insert new variables into existing groups"""

    (init_time, model, system, domain, frequency, background) = analysis

    xr.testing.assert_equal(
        xr.open_zarr(
            zarr_file,
            group=(
                f"{model}/{system}/{domain}/{background}/{frequency}/"
                f"ps/{init_time}/anl"
            ),
        ),
        ps_anl,
    )

    xr.testing.assert_equal(
        xr.open_zarr(
            zarr_file,
            group=(
                f"{model}/{system}/{domain}/{background}/{frequency}/"
                f"t/{init_time}/anl"
            ),
        ),
        t_anl,
    )

    analysis_count = session.scalar(select(func.count()).select_from(Analysis))
    assert analysis_count == 1
