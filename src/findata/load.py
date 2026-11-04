"""Idempotent loads into the raw schema: upsert on the natural key of each source."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import date

import psycopg

from findata.config import FredSeries
from findata.extract.ecb import ExchangeRate
from findata.extract.fred import Observation

# `where ... is distinct from` skips rows whose value did not change, so _loaded_at
# keeps meaning "last time this value changed" and re-runs do not rewrite the table.
_UPSERT_EXCHANGE_RATES = """
    insert into raw.ecb_exchange_rates (currency, rate_date, rate, _batch_id)
    values (%s, %s, %s, %s)
    on conflict (currency, rate_date) do update
        set rate = excluded.rate, _batch_id = excluded._batch_id, _loaded_at = now()
        where raw.ecb_exchange_rates.rate is distinct from excluded.rate
"""

_UPSERT_FRED_OBSERVATIONS = """
    insert into raw.fred_observations (series_id, observation_date, value, _batch_id)
    values (%s, %s, %s, %s)
    on conflict (series_id, observation_date) do update
        set value = excluded.value, _batch_id = excluded._batch_id, _loaded_at = now()
        where raw.fred_observations.value is distinct from excluded.value
"""

_UPSERT_FRED_SERIES = """
    insert into raw.fred_series (series_id, series_name, units, frequency, category)
    values (%s, %s, %s, %s, %s)
    on conflict (series_id) do update
        set series_name = excluded.series_name, units = excluded.units,
            frequency = excluded.frequency, category = excluded.category, _loaded_at = now()
"""


def upsert_exchange_rates(
    conn: psycopg.Connection, rates: Iterable[ExchangeRate], batch_id: str
) -> int:
    rows = [(r.currency, r.rate_date, r.rate, batch_id) for r in rates]
    with conn.cursor() as cur:
        cur.executemany(_UPSERT_EXCHANGE_RATES, rows)
    return len(rows)


def upsert_fred_observations(
    conn: psycopg.Connection, observations: Iterable[Observation], batch_id: str
) -> int:
    rows = [(o.series_id, o.observation_date, o.value, batch_id) for o in observations]
    with conn.cursor() as cur:
        cur.executemany(_UPSERT_FRED_OBSERVATIONS, rows)
    return len(rows)


def upsert_fred_series(conn: psycopg.Connection, series: Iterable[FredSeries]) -> None:
    rows = [(s.id, s.name, s.units, s.frequency, s.category) for s in series]
    with conn.cursor() as cur:
        cur.executemany(_UPSERT_FRED_SERIES, rows)


def latest_exchange_rate_date(conn: psycopg.Connection) -> date | None:
    return conn.execute("select max(rate_date) from raw.ecb_exchange_rates").fetchone()[0]


def latest_fred_observation_date(conn: psycopg.Connection, series_id: str) -> date | None:
    return conn.execute(
        "select max(observation_date) from raw.fred_observations where series_id = %s",
        (series_id,),
    ).fetchone()[0]


class RunStats:
    def __init__(self) -> None:
        self.rows_loaded = 0


@contextmanager
def logged_run(
    conn: psycopg.Connection, batch_id: str, source: str, start_date: date | None
) -> Iterator[RunStats]:
    """Record a run in raw.ingestion_log and commit (or roll back) the data it loaded.

    The 'running' row is committed first so that a crash still leaves a trace.
    """
    conn.execute(
        "insert into raw.ingestion_log (batch_id, source, start_date, status)"
        " values (%s, %s, %s, 'running')",
        (batch_id, source, start_date),
    )
    conn.commit()

    stats = RunStats()
    try:
        yield stats
    except Exception as exc:
        conn.rollback()
        conn.execute(
            "update raw.ingestion_log set status = 'failed', finished_at = now(),"
            " error_message = %s where batch_id = %s and source = %s",
            (str(exc)[:2000], batch_id, source),
        )
        conn.commit()
        raise
    else:
        conn.execute(
            "update raw.ingestion_log set status = 'success', finished_at = now(),"
            " rows_loaded = %s where batch_id = %s and source = %s",
            (stats.rows_loaded, batch_id, source),
        )
        conn.commit()
