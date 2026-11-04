from datetime import date
from decimal import Decimal

from findata.config import EcbConfig
from findata.extract import ecb

# Trimmed ECB "csvdata" response (real responses have ~30 columns)
SAMPLE = """KEY,FREQ,CURRENCY,CURRENCY_DENOM,EXR_TYPE,EXR_SUFFIX,TIME_PERIOD,OBS_VALUE,OBS_STATUS
EXR.D.GBP.EUR.SP00.A,D,GBP,EUR,SP00,A,2026-10-20,0.84028,A
EXR.D.GBP.EUR.SP00.A,D,GBP,EUR,SP00,A,2026-10-21,0.83825,A
EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-10-20,1.1612,A
EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-10-21,,A
"""

CFG = EcbConfig(
    base_url="https://data-api.ecb.europa.eu/service/data/EXR",
    currencies=("USD", "GBP"),
    lookback_days=7,
)


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self.response


def test_build_url_joins_currencies():
    assert ecb.build_url(CFG.base_url, CFG.currencies) == (
        "https://data-api.ecb.europa.eu/service/data/EXR/D.USD+GBP.EUR.SP00.A"
    )


def test_parse_csv_returns_typed_records():
    rates = ecb.parse_csv(SAMPLE)

    assert rates[0] == ecb.ExchangeRate("GBP", date(2026, 10, 20), Decimal("0.84028"))
    assert {r.currency for r in rates} == {"GBP", "USD"}


def test_parse_csv_skips_missing_values():
    rates = ecb.parse_csv(SAMPLE)

    assert len(rates) == 3
    assert not any(r.currency == "USD" and r.rate_date == date(2026, 10, 21) for r in rates)


def test_parse_csv_empty_body():
    assert ecb.parse_csv("") == []


def test_fetch_sends_period_params():
    session = FakeSession(FakeResponse(SAMPLE))

    rates = ecb.fetch(CFG, date(2026, 10, 20), date(2026, 10, 21), session=session)

    url, params = session.calls[0]
    assert url.endswith("/D.USD+GBP.EUR.SP00.A")
    assert params == {"format": "csvdata", "startPeriod": "2026-10-20", "endPeriod": "2026-10-21"}
    assert len(rates) == 3


def test_fetch_treats_404_as_no_data():
    # The ECB answers 404 when the requested period has no observations yet
    session = FakeSession(FakeResponse("No results found", status_code=404))

    assert ecb.fetch(CFG, date(2026, 11, 2), session=session) == []
