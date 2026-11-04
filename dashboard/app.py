"""Macro & FX Monitor — reads only from the dbt marts."""

from __future__ import annotations

import os
from datetime import date, timedelta

import pandas as pd
import psycopg
import streamlit as st

st.set_page_config(page_title="Macro & FX Monitor", page_icon="📈", layout="wide")


@st.cache_data(ttl=600)
def query(sql: str, params: tuple | None = None) -> pd.DataFrame:
    with psycopg.connect(os.environ.get("WAREHOUSE_DSN", "")) as conn:
        cur = conn.execute(sql, params)
        return pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])


def pct(value: float | None, digits: int = 1) -> str:
    return "n/a" if value is None or pd.isna(value) else f"{value:.{digits}%}"


st.title("Macro & FX Monitor")
st.caption(
    "EUR reference rates (European Central Bank) and US macro indicators (FRED, Federal "
    "Reserve Bank of St. Louis). Independent portfolio project — not investment advice."
)

try:
    fx = query(
        """
        select f.currency_code, c.currency_name, f.rate_date,
               f.eur_rate::float as eur_rate, f.daily_return::float as daily_return,
               f.volatility_20d_annualised::float as volatility
        from marts.fct_fx_rates_daily f
        join marts.dim_currency c using (currency_code)
        order by f.rate_date
        """
    )
    monthly = query(
        """
        select month_start, eur_usd_avg::float, us_cpi_yoy_pct::float,
               us_unemployment_rate::float, us_fed_funds_rate::float,
               us_10y_treasury_yield::float
        from marts.rpt_macro_fx_monthly
        order by month_start
        """
    )
except psycopg.errors.UndefinedTable:
    st.info("The marts are not built yet. Trigger the `findata_daily` DAG in Airflow first.")
    st.stop()

if fx.empty:
    st.info("No data loaded yet. Trigger the `findata_daily` DAG in Airflow first.")
    st.stop()

# --- KPIs ---------------------------------------------------------------------------------
usd = fx[fx.currency_code == "USD"]
latest_usd = usd.iloc[-1]
latest_cpi = monthly.dropna(subset=["us_cpi_yoy_pct"]).iloc[-1]
latest_rates = monthly.dropna(subset=["us_fed_funds_rate"]).iloc[-1]

k1, k2, k3, k4 = st.columns(4)
k1.metric(
    f"EUR/USD · {latest_usd.rate_date:%d %b %Y}",
    f"{latest_usd.eur_rate:.4f}",
    pct(latest_usd.daily_return, 2),
)
k2.metric("EUR/USD 20-day volatility (ann.)", pct(latest_usd.volatility))
k3.metric(f"US CPI YoY · {latest_cpi.month_start:%b %Y}", pct(latest_cpi.us_cpi_yoy_pct))
k4.metric(
    f"Fed Funds rate · {latest_rates.month_start:%b %Y}",
    f"{latest_rates.us_fed_funds_rate:.2f}%",
)

# --- FX -----------------------------------------------------------------------------------
st.header("Euro exchange rates")

c1, c2 = st.columns([3, 1])
currencies = c1.multiselect(
    "Currencies", sorted(fx.currency_code.unique()), default=["USD", "GBP", "CHF"]
)
period = c2.radio("Period", ["1Y", "3Y", "All"], horizontal=True, index=1)

start = {
    "1Y": date.today() - timedelta(days=365),
    "3Y": date.today() - timedelta(days=3 * 365),
    "All": fx.rate_date.min(),
}[period]
selected = fx[fx.currency_code.isin(currencies) & (fx.rate_date >= start)]

if selected.empty:
    st.warning("Select at least one currency.")
else:
    rates = selected.pivot(index="rate_date", columns="currency_code", values="eur_rate")
    # Rebased to 100 so currencies with very different levels (JPY vs GBP) are comparable
    rebased = rates / rates.bfill().iloc[0] * 100
    st.subheader("Rate per 1 EUR, rebased to 100 (up = euro stronger)")
    st.line_chart(rebased)

    st.subheader("20-day annualised volatility")
    st.line_chart(selected.pivot(index="rate_date", columns="currency_code", values="volatility"))

# --- Macro --------------------------------------------------------------------------------
st.header("US macro environment vs EUR/USD")

m1, m2 = st.columns(2)
with m1:
    st.subheader("Interest rates (%)")
    st.line_chart(
        monthly.set_index("month_start")[["us_fed_funds_rate", "us_10y_treasury_yield"]]
    )
with m2:
    st.subheader("EUR/USD monthly average")
    st.line_chart(monthly.set_index("month_start")[["eur_usd_avg"]])

st.subheader("Last 12 months")
st.dataframe(
    monthly.tail(12).iloc[::-1],
    hide_index=True,
    column_config={
        "month_start": st.column_config.DateColumn("Month", format="MMM YYYY"),
        "eur_usd_avg": st.column_config.NumberColumn("EUR/USD avg", format="%.4f"),
        "us_cpi_yoy_pct": st.column_config.NumberColumn("CPI YoY", format="percent"),
        "us_unemployment_rate": st.column_config.NumberColumn("Unemployment %", format="%.1f"),
        "us_fed_funds_rate": st.column_config.NumberColumn("Fed Funds %", format="%.2f"),
        "us_10y_treasury_yield": st.column_config.NumberColumn("10Y yield %", format="%.2f"),
    },
)
