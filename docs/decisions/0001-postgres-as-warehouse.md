# ADR 0001 — PostgreSQL as the warehouse

**Status:** accepted

## Context
Data volume is small (tens of thousands of rows per year). The platform must run locally with one command and be free.

## Options considered
- **PostgreSQL** — mature, runs in Docker, first-class dbt adapter, also hosts Airflow metadata.
- **DuckDB** — excellent for analytics, but a single-writer file is awkward when Airflow, dbt and the dashboard run in separate processes/containers.
- **Cloud warehouse (BigQuery, Snowflake)** — closer to many production setups, but needs accounts and credentials, which breaks NFR-2 (reproducibility without keys).

## Decision
PostgreSQL 16. One container, two databases (`warehouse`, `airflow`).

## Consequences
- Zero-cost, fully reproducible setup.
- Window functions and `generate_series` cover all modelling needs.
- Moving to a cloud warehouse later mainly means changing the dbt adapter and the loader connection; SQL is kept close to ANSI.
