"""Load source configuration (config/sources.yml) and runtime settings from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

# Repository root when running from a checkout; overridden with FINDATA_CONFIG in containers.
_DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "sources.yml"


@dataclass(frozen=True)
class FredSeries:
    id: str
    name: str
    units: str
    frequency: str
    category: str


@dataclass(frozen=True)
class EcbConfig:
    base_url: str
    currencies: tuple[str, ...]
    lookback_days: int


@dataclass(frozen=True)
class FredConfig:
    base_url: str
    lookback_days: int
    series: tuple[FredSeries, ...]


@dataclass(frozen=True)
class Settings:
    ecb: EcbConfig
    fred: FredConfig
    start_date: date


def load_settings(path: str | Path | None = None) -> Settings:
    config_path = Path(path or os.environ.get("FINDATA_CONFIG", _DEFAULT_CONFIG))
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    ecb = raw["ecb"]
    fred = raw["fred"]
    return Settings(
        ecb=EcbConfig(
            base_url=ecb["base_url"],
            currencies=tuple(ecb["currencies"]),
            lookback_days=int(ecb["lookback_days"]),
        ),
        fred=FredConfig(
            base_url=fred["base_url"],
            lookback_days=int(fred["lookback_days"]),
            series=tuple(FredSeries(**s) for s in fred["series"]),
        ),
        start_date=date.fromisoformat(os.environ.get("FINDATA_START_DATE", "2015-01-01")),
    )
