# Requirements & Acceptance Criteria

## 1. Business context

A (fictional) treasury & strategy team of a euro-area company with costs and revenues in several currencies wants a single, trusted place to monitor:

- **FX exposure** — how the euro moves against the currencies the company trades in, and how volatile those moves are;
- **US macro indicators** — inflation, unemployment and interest rates, in the same place as the FX data.

Today the analysts download CSV files by hand from the ECB and FRED websites and paste them into spreadsheets. This is slow, error-prone and not auditable.

## 2. Goal

Build an automated, reproducible ELT platform that ingests public FX and macro data daily, models it into analysis-ready tables, tests data quality, and serves a dashboard.

## 3. Stakeholders (personas)

| Persona | Need |
|---|---|
| Treasury analyst | Daily EUR exchange rates, returns and volatility per currency |
| Strategy analyst | Monthly macro indicators with MoM / YoY changes |
| Data engineer (owner) | Pipelines that are idempotent, observable and easy to extend |

## 4. Scope

**In scope:** ECB euro reference rates (5 currencies), 4 FRED macro series, daily orchestration, dimensional model, data tests, dashboard, CI.

**Out of scope (v1):** intraday data, forecasting, user authentication, cloud deployment.

## 5. Functional requirements

| ID | Requirement |
|---|---|
| FR-1 | Ingest daily ECB reference rates for USD, GBP, JPY, CHF, CNY against EUR. |
| FR-2 | Ingest FRED series CPIAUCSL, UNRATE, FEDFUNDS, DGS10. |
| FR-3 | Sources (currencies, series) are configurable without code changes. |
| FR-4 | Runs are incremental: only new data plus a configurable look-back window is re-read. |
| FR-5 | Provide a daily FX fact table with daily return and 20-day annualised volatility. |
| FR-6 | Provide a monthly macro fact table with MoM and YoY changes. |
| FR-7 | Provide a monthly reporting table combining FX and macro indicators. |
| FR-8 | Provide a dashboard showing the latest KPIs and historical trends. |

## 6. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-1 | **Idempotency:** re-running a load for the same period never creates duplicates. |
| NFR-2 | **Reproducibility:** the whole stack starts with one command (`docker compose up`); no API keys required. |
| NFR-3 | **Data quality:** keys, nulls, referential integrity and value ranges are tested on every run. |
| NFR-4 | **Observability:** every ingestion run is logged (source, rows, status, duration). |
| NFR-5 | **Resilience:** transient HTTP errors are retried with back-off. |
| NFR-6 | **Quality gate:** linting, unit tests and the dbt build run in CI on every push. |

## 7. Acceptance criteria

- [ ] `docker compose up` starts PostgreSQL, Airflow and the dashboard with no manual steps.
- [ ] Triggering the `findata_daily` DAG loads data from both sources and builds all dbt models.
- [ ] Running the DAG twice in a row leaves row counts in `raw` unchanged (NFR-1).
- [ ] `dbt build` passes all tests.
- [ ] Each run writes one row per source into `raw.ingestion_log`.
- [ ] The dashboard shows the latest EUR/USD rate, its 20-day volatility and the latest US CPI YoY.
- [ ] CI is green: ruff, pytest and `dbt build` on bundled sample data.
