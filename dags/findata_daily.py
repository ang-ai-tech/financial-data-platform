"""Daily ELT: ingest ECB + FRED into raw, then build and test the dbt models.

ECB reference rates are published around 16:00 CET on TARGET working days,
so the DAG runs on weekday evenings.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import dag, task

DBT = "/opt/dbt-venv/bin/dbt"
DBT_DIR = "/opt/airflow/dbt"


@dag(
    dag_id="findata_daily",
    schedule="0 18 * * 1-5",
    start_date=datetime(2026, 1, 1),
    catchup=False,  # loads are incremental by data, not by logical date
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["findata", "elt"],
    doc_md=__doc__,
)
def findata_daily():
    @task
    def init_db() -> None:
        from findata import db

        with db.connect() as conn:
            db.init_schema(conn)

    @task
    def ingest_ecb(run_id: str | None = None) -> int:
        from findata import db, pipeline
        from findata.config import load_settings

        with db.connect() as conn:
            return pipeline.ingest_ecb(load_settings(), conn, batch_id=run_id)

    @task
    def ingest_fred(run_id: str | None = None) -> int:
        from findata import db, pipeline
        from findata.config import load_settings

        with db.connect() as conn:
            return pipeline.ingest_fred(load_settings(), conn, batch_id=run_id)

    dbt_build = BashOperator(
        task_id="dbt_build",
        # `build` runs seeds, models and tests in DAG order; a failing test stops downstream models
        bash_command=f"cd {DBT_DIR} && {DBT} build --profiles-dir .",
    )

    init_db() >> [ingest_ecb(), ingest_fred()] >> dbt_build


findata_daily()
