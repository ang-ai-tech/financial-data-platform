"""FRED economic series via the public graph CSV endpoint (no API key, see ADR 0002).

Response format:
    observation_date,<SERIES_ID>
    2024-01-01,3.7
    2024-01-02,          <- missing value (e.g. bond market holiday)
"""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import requests

from findata.config import FredConfig
from findata.httpclient import build_session, get_text

log = logging.getLogger(__name__)

_MISSING_VALUES = {"", "."}


@dataclass(frozen=True)
class Observation:
    series_id: str
    observation_date: date
    value: Decimal


def parse_csv(text: str, series_id: str) -> list[Observation]:
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if header is None:
        return []
    if len(header) != 2 or header[1] != series_id:
        raise ValueError(f"Unexpected FRED header for {series_id}: {header}")

    observations = []
    for observation_date, value in reader:
        value = value.strip()
        if value in _MISSING_VALUES:
            continue
        observations.append(
            Observation(
                series_id=series_id,
                observation_date=date.fromisoformat(observation_date),
                value=Decimal(value),
            )
        )
    return observations


def fetch(
    cfg: FredConfig,
    series_id: str,
    start: date,
    end: date | None = None,
    session: requests.Session | None = None,
) -> list[Observation]:
    params = {"id": series_id, "cosd": start.isoformat()}
    if end:
        params["coed"] = end.isoformat()

    text = get_text(session or build_session(), cfg.base_url, params)
    observations = parse_csv(text, series_id)
    log.info("FRED: fetched %d observations for %s since %s", len(observations), series_id, start)
    return observations
