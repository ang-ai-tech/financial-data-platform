from datetime import date
from decimal import Decimal

import pytest

from findata.extract import fred

SAMPLE = """observation_date,DGS10
2026-09-01,4.79
2026-09-02,4.79
2026-09-07,
2026-09-08,.
2026-09-09,4.83
"""


def test_parse_csv_returns_typed_records():
    observations = fred.parse_csv(SAMPLE, "DGS10")

    assert observations[0] == fred.Observation("DGS10", date(2026, 9, 1), Decimal("4.79"))
    assert observations[-1].observation_date == date(2026, 9, 9)


def test_parse_csv_skips_empty_and_dot_values():
    observations = fred.parse_csv(SAMPLE, "DGS10")

    assert [o.observation_date.day for o in observations] == [1, 2, 9]


def test_parse_csv_rejects_unexpected_series():
    with pytest.raises(ValueError, match="Unexpected FRED header"):
        fred.parse_csv(SAMPLE, "UNRATE")


def test_parse_csv_empty_body():
    assert fred.parse_csv("", "DGS10") == []
