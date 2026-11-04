from datetime import date

from findata.config import load_settings
from findata.pipeline import new_batch_id, resolve_start

DEFAULT_START = date(2015, 1, 1)


def test_resolve_start_empty_warehouse_uses_default():
    assert resolve_start(None, 7, DEFAULT_START) == DEFAULT_START


def test_resolve_start_applies_lookback():
    assert resolve_start(date(2026, 10, 30), 7, DEFAULT_START) == date(2026, 10, 23)


def test_resolve_start_never_before_default():
    assert resolve_start(date(2015, 1, 3), 120, DEFAULT_START) == DEFAULT_START


def test_resolve_start_full_refresh():
    assert resolve_start(date(2026, 10, 30), 7, DEFAULT_START, full_refresh=True) == DEFAULT_START


def test_resolve_start_override_wins():
    override = date(2020, 6, 1)
    assert resolve_start(date(2026, 10, 30), 7, DEFAULT_START, override=override) == override


def test_batch_ids_are_unique():
    assert new_batch_id() != new_batch_id()


def test_repository_config_is_valid():
    settings = load_settings()

    assert "USD" in settings.ecb.currencies
    assert {s.id for s in settings.fred.series} >= {"CPIAUCSL", "DGS10"}
    assert all(s.frequency in {"daily", "monthly"} for s in settings.fred.series)
