"""Ingestion use cases, shared by the CLI and the Airflow DAG."""

from __future__ import annotations

import csv
import logging
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import psycopg
import requests

from findata import load
from findata.config import Settings
from findata.extract import ecb, fred
from findata.httpclient import build_session

log = logging.getLogger(__name__)

ECB_SAMPLE_FILE = "ecb_exchange_rates.csv"
FRED_SAMPLE_FILE = "fred_observations.csv"


def new_batch_id() -> str:
    return f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:6]}"


def resolve_start(
    latest_loaded: date | None,
    lookback_days: int,
    default_start: date,
    *,
    full_refresh: bool = False,
    override: date | None = None,
) -> date:
    """Where the next incremental load should start.

    An explicit override wins; otherwise re-read `lookback_days` before the latest loaded
    date to pick up late or revised values, never going before `default_start`.
    """
    if override:
        return override
    if full_refresh or latest_loaded is None:
        return default_start
    return max(default_start, latest_loaded - timedelta(days=lookback_days))


def ingest_ecb(
    settings: Settings,
    conn: psycopg.Connection,
    *,
    batch_id: str | None = None,
    start: date | None = None,
    full_refresh: bool = False,
    session: requests.Session | None = None,
) -> int:
    batch_id = batch_id or new_batch_id()
    start = resolve_start(
        load.latest_exchange_rate_date(conn),
        settings.ecb.lookback_days,
        settings.start_date,
        full_refresh=full_refresh,
        override=start,
    )
    with load.logged_run(conn, batch_id, "ecb", start) as stats:
        rates = ecb.fetch(settings.ecb, start, session=session)
        stats.rows_loaded = load.upsert_exchange_rates(conn, rates, batch_id)
    return stats.rows_loaded


def ingest_fred(
    settings: Settings,
    conn: psycopg.Connection,
    *,
    batch_id: str | None = None,
    start: date | None = None,
    full_refresh: bool = False,
    session: requests.Session | None = None,
) -> int:
    batch_id = batch_id or new_batch_id()
    session = session or build_session()
    with load.logged_run(conn, batch_id, "fred", start) as stats:
        load.upsert_fred_series(conn, settings.fred.series)
        for series in settings.fred.series:
            series_start = resolve_start(
                load.latest_fred_observation_date(conn, series.id),
                settings.fred.lookback_days,
                settings.start_date,
                full_refresh=full_refresh,
                override=start,
            )
            observations = fred.fetch(settings.fred, series.id, series_start, session=session)
            stats.rows_loaded += load.upsert_fred_observations(conn, observations, batch_id)
    return stats.rows_loaded


def export_sample(settings: Settings, out_dir: Path, start: date) -> None:
    """Snapshot a small slice of real data to CSV, used by CI and offline demos."""
    out_dir.mkdir(parents=True, exist_ok=True)
    session = build_session()

    rates = ecb.fetch(settings.ecb, start, session=session)
    with (out_dir / ECB_SAMPLE_FILE).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["currency", "rate_date", "rate"])
        writer.writerows((r.currency, r.rate_date, r.rate) for r in rates)

    with (out_dir / FRED_SAMPLE_FILE).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["series_id", "observation_date", "value"])
        for series in settings.fred.series:
            observations = fred.fetch(settings.fred, series.id, start, session=session)
            writer.writerows((o.series_id, o.observation_date, o.value) for o in observations)


def load_sample(settings: Settings, conn: psycopg.Connection, sample_dir: Path) -> int:
    """Load the CSV snapshot produced by export_sample, through the same upsert path."""
    batch_id = f"sample-{new_batch_id()}"
    with (sample_dir / ECB_SAMPLE_FILE).open(encoding="utf-8") as f:
        rates = [
            ecb.ExchangeRate(row["currency"], date.fromisoformat(row["rate_date"]),
                             Decimal(row["rate"]))
            for row in csv.DictReader(f)
        ]
    with (sample_dir / FRED_SAMPLE_FILE).open(encoding="utf-8") as f:
        observations = [
            fred.Observation(row["series_id"], date.fromisoformat(row["observation_date"]),
                             Decimal(row["value"]))
            for row in csv.DictReader(f)
        ]

    with load.logged_run(conn, batch_id, "sample", None) as stats:
        load.upsert_fred_series(conn, settings.fred.series)
        stats.rows_loaded = load.upsert_exchange_rates(conn, rates, batch_id)
        stats.rows_loaded += load.upsert_fred_observations(conn, observations, batch_id)
    return stats.rows_loaded
