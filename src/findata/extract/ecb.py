"""ECB euro foreign exchange reference rates (SDMX REST API, dataset EXR).

Series key: EXR.D.<CURRENCY>.EUR.SP00.A = daily, units of <CURRENCY> per 1 EUR.
"""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import requests

from findata.config import EcbConfig
from findata.httpclient import build_session, get_text

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExchangeRate:
    currency: str
    rate_date: date
    rate: Decimal  # units of `currency` per 1 EUR


def build_url(base_url: str, currencies: tuple[str, ...]) -> str:
    return f"{base_url}/D.{'+'.join(currencies)}.EUR.SP00.A"


def parse_csv(text: str) -> list[ExchangeRate]:
    if not text.strip():
        return []

    rates = []
    for row in csv.DictReader(io.StringIO(text)):
        value = (row.get("OBS_VALUE") or "").strip()
        if not value:
            # The ECB publishes no rate on TARGET holidays; an empty value is not an error.
            continue
        rates.append(
            ExchangeRate(
                currency=row["CURRENCY"],
                rate_date=date.fromisoformat(row["TIME_PERIOD"]),
                rate=Decimal(value),
            )
        )
    return rates


def fetch(
    cfg: EcbConfig,
    start: date,
    end: date | None = None,
    session: requests.Session | None = None,
) -> list[ExchangeRate]:
    params = {"format": "csvdata", "startPeriod": start.isoformat()}
    if end:
        params["endPeriod"] = end.isoformat()

    text = get_text(
        session or build_session(),
        build_url(cfg.base_url, cfg.currencies),
        params,
        empty_on_404=True,
    )
    rates = parse_csv(text)
    log.info("ECB: fetched %d rates for %s since %s", len(rates), ",".join(cfg.currencies), start)
    return rates
