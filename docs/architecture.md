# Architecture

```mermaid
flowchart LR
    subgraph Sources["Public sources"]
        ECB["ECB Data Portal<br/>SDMX REST API"]
        FRED["FRED<br/>graph CSV endpoint"]
    end

    subgraph Airflow["Apache Airflow — DAG findata_daily"]
        I1["ingest_ecb"]
        I2["ingest_fred"]
        D["dbt build"]
    end

    subgraph PG["PostgreSQL — warehouse"]
        RAW[("raw<br/>append/upsert, as delivered")]
        STG[("staging<br/>typed, renamed")]
        INT[("intermediate<br/>business logic")]
        MRT[("marts<br/>dims · facts · reports")]
    end

    ECB --> I1 --> RAW
    FRED --> I2 --> RAW
    RAW --> D
    D --> STG --> INT --> MRT
    MRT --> DASH["Streamlit dashboard"]
    MRT --> PBI["Power BI report"]
```

## Layers

| Layer | Owner | Materialisation | Purpose |
|---|---|---|---|
| `raw` | Python (`findata`) | tables, upsert on natural key | Data exactly as delivered + load metadata (`_loaded_at`, `_batch_id`) |
| `staging` | dbt | views | 1:1 with sources: rename, cast, no business logic |
| `intermediate` | dbt | views | Reusable logic: returns, volatility, monthly aggregation |
| `marts` | dbt | tables | Star schema for BI: `dim_*`, `fct_*`, `rpt_*` |

## Data model (marts)

```mermaid
erDiagram
    dim_date ||--o{ fct_fx_rates_daily : "rate_date"
    dim_currency ||--o{ fct_fx_rates_daily : "currency_code"
    dim_date ||--o{ fct_macro_indicators_monthly : "month_start"
    dim_indicator ||--o{ fct_macro_indicators_monthly : "series_id"

    fct_fx_rates_daily {
        text currency_code PK
        date rate_date PK
        numeric eur_rate
        numeric daily_return
        numeric volatility_20d_annualised
    }
    fct_macro_indicators_monthly {
        text series_id PK
        date month_start PK
        numeric value
        numeric mom_change
        numeric yoy_change
        numeric yoy_pct_change
    }
    dim_currency {
        text currency_code PK
        text currency_name
        text region
    }
    dim_indicator {
        text series_id PK
        text series_name
        text units
        text frequency
        text category
    }
    dim_date {
        date date_day PK
        int year
        int quarter
        int month
        boolean is_weekend
    }
```

`rpt_macro_fx_monthly` is a wide, denormalised table (one row per month) built for the dashboard.

## Incremental ingestion

On every run the loader asks the warehouse for the latest date already loaded per source and re-reads from `latest_date - lookback_days`:

- ECB: 7 days (late publications are rare but possible);
- FRED: 120 days (macro series are **revised** after first release).

Rows are upserted on the natural key (`currency, rate_date` / `series_id, observation_date`), so re-reading overlapping windows is safe. `--full-refresh` reloads from `FINDATA_START_DATE`.

## Runtime (Docker Compose)

| Service | Image | Port |
|---|---|---|
| `postgres` | `postgres:16` | 5432 — databases `warehouse` and `airflow` |
| `airflow` | custom, based on `apache/airflow:3.3.2-python3.12` | 8080 |
| `dashboard` | custom, `python:3.12-slim` + Streamlit | 8501 |

dbt runs inside the Airflow container from an isolated virtualenv (`/opt/dbt-venv`) — see ADR 0004.
