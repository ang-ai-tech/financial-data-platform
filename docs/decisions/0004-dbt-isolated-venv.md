# ADR 0004 — Run dbt from an isolated virtualenv inside the Airflow image

**Status:** accepted

## Context
Airflow and dbt both have large dependency trees. Installing them into the same Python environment frequently causes version conflicts and makes upgrades risky.

## Options considered
- Same environment as Airflow — simplest, but fragile.
- Separate dbt container triggered by Airflow (DockerOperator / Kubernetes) — the cleanest isolation in production, but needs the Docker socket mounted into Airflow, which is a security concern on a laptop.
- **Isolated virtualenv in the Airflow image** — dbt lives in `/opt/dbt-venv` and is called through `BashOperator`.

## Decision
Isolated virtualenv. The `findata` package is installed into Airflow's own environment (it has only three light dependencies).

## Consequences
- Airflow and dbt can be upgraded independently.
- In a production deployment this would be replaced by a dedicated dbt container or a managed dbt service.
