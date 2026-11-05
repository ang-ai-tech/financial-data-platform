# Power BI Report — Work in Progress

This folder contains the implementation guide and design specifications for a planned Power BI report built on the same dbt marts used by the Streamlit
dashboard.

The report will reuse the existing dimensional model, with PostgreSQL as the data source in Import mode.

The `.pbix` file and report screenshots will be added once the implementation is complete.


A Power BI report built on the same dbt **marts** used by the Streamlit dashboard: one dimensional model, two consumers.

| | Streamlit | Power BI |
|---|---|---|
| Audience | Anyone cloning the repo | Business users |
| Runs from | `docker compose up` | Power BI Desktop (Windows) |
| Data access | Live query on the marts | Import mode from the marts |

File: `FinancialDataPlatform.pbix` (Import mode, public data only).

## 1. Connect

Start the stack (`docker compose up -d`) and run the `findata_daily` DAG once, then in Power BI Desktop:

1. **Get data → PostgreSQL database**
2. Server: `localhost:5432` · Database: `warehouse` · Data connectivity mode: **Import**
3. Credentials (*Database* tab): user `findata`, password `findata`
4. Select the tables below from the `marts` schema.

> The local PostgreSQL container has no SSL certificate. If Power BI reports a certificate/encryption error:
> *File → Options and settings → Data source settings → localhost:5432;warehouse → Edit permissions →* untick **Encrypt connections**.

## 2. Tables

| Table | Role |
|---|---|
| `marts.dim_date` | Date dimension — *Mark as date table* on `date_day` |
| `marts.dim_currency` | Currency dimension |
| `marts.dim_indicator` | Indicator dimension |
| `marts.fct_fx_rates_daily` | Fact: daily FX rates |
| `marts.fct_macro_indicators_monthly` | Fact: monthly indicators |

Rename them in Power BI without the `marts ` prefix (e.g. `fct_fx_rates_daily`).

## 3. Relationships (star schema)

All one-to-many, single direction, from dimension to fact:

| From (1) | To (*) |
|---|---|
| `dim_date[date_day]` | `fct_fx_rates_daily[rate_date]` |
| `dim_currency[currency_code]` | `fct_fx_rates_daily[currency_code]` |
| `dim_date[date_day]` | `fct_macro_indicators_monthly[month_start]` |
| `dim_indicator[series_id]` | `fct_macro_indicators_monthly[series_id]` |

Hide the key columns on the fact tables so report authors always filter through the dimensions.

## 4. Measures (DAX)

Create an empty table `_Measures` (*Enter data* → one column, then hide it) and add:

```dax
Latest Rate Date = MAX ( fct_fx_rates_daily[rate_date] )

EUR Rate (Latest) =
VAR LastDate = [Latest Rate Date]
RETURN
    CALCULATE ( AVERAGE ( fct_fx_rates_daily[eur_rate] ), fct_fx_rates_daily[rate_date] = LastDate )

EUR Rate (Average) = AVERAGE ( fct_fx_rates_daily[eur_rate] )

Period Change % =
VAR FirstDate = MIN ( fct_fx_rates_daily[rate_date] )
VAR LastDate = MAX ( fct_fx_rates_daily[rate_date] )
VAR FirstRate =
    CALCULATE ( AVERAGE ( fct_fx_rates_daily[eur_rate] ), fct_fx_rates_daily[rate_date] = FirstDate )
VAR LastRate =
    CALCULATE ( AVERAGE ( fct_fx_rates_daily[eur_rate] ), fct_fx_rates_daily[rate_date] = LastDate )
RETURN
    DIVIDE ( LastRate, FirstRate ) - 1

Volatility 20d (Latest) =
VAR LastDate = [Latest Rate Date]
RETURN
    CALCULATE (
        AVERAGE ( fct_fx_rates_daily[volatility_20d_annualised] ),
        fct_fx_rates_daily[rate_date] = LastDate
    )

Indicator Value (Latest) =
VAR LastMonth = MAX ( fct_macro_indicators_monthly[month_start] )
RETURN
    CALCULATE (
        AVERAGE ( fct_macro_indicators_monthly[value] ),
        fct_macro_indicators_monthly[month_start] = LastMonth
    )

US CPI YoY (Latest) =
VAR LastMonth =
    CALCULATE (
        MAX ( fct_macro_indicators_monthly[month_start] ),
        dim_indicator[series_id] = "CPIAUCSL",
        NOT ISBLANK ( fct_macro_indicators_monthly[yoy_pct_change] )
    )
RETURN
    CALCULATE (
        AVERAGE ( fct_macro_indicators_monthly[yoy_pct_change] ),
        dim_indicator[series_id] = "CPIAUCSL",
        fct_macro_indicators_monthly[month_start] = LastMonth
    )
```

Formats: `Period Change %`, `Volatility 20d (Latest)`, `US CPI YoY (Latest)` → Percentage, 1 decimal. `EUR Rate (*)` → Decimal, 4 decimals.

> `EUR Rate (Latest)` and `Volatility 20d (Latest)` are meant for **one currency at a time** (single-select slicer).
> `Indicator Value (Latest)` is meant for **one indicator at a time** (visual-level filter on `dim_indicator[series_id]`).

## 5. Report pages

### Page 1 — Overview
- **Slicers:** `dim_date[date_day]` (Between), `dim_currency[currency_name]` (single select, default *US dollar*)
- **Cards:** EUR Rate (Latest) · Period Change % · Volatility 20d (Latest) · US CPI YoY (Latest) · Indicator Value (Latest) filtered to `UNRATE` · Indicator Value (Latest) filtered to `FEDFUNDS`
- **Line chart:** X `dim_date[date_day]`, Y `EUR Rate (Average)`
- **Line chart:** X `dim_date[month_start]`, Y `Indicator Value (Latest)`, Legend `dim_indicator[series_name]`, filtered to category `interest_rates`

### Page 2 — FX Risk
- **Slicer:** `dim_date[date_day]` (Between)
- **Line chart:** X `dim_date[date_day]`, Y `fct_fx_rates_daily[volatility_20d_annualised]` (Average), Legend `dim_currency[currency_code]`
- **Matrix:** Rows `dim_currency[currency_name]`, Columns `dim_date[year]`, Values `Period Change %` (conditional formatting: red/green background)
- **Bar chart:** Y `dim_currency[currency_code]`, X `Volatility 20d (Latest)`

## 6. Screenshots

Export each page (*File → Export → Export to PDF*, or a screenshot) to `docs/img/powerbi-overview.png` and `docs/img/powerbi-fx-risk.png`; they are referenced from the main README.
