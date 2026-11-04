FROM apache/airflow:3.3.2-python3.12

# dbt lives in its own virtualenv to avoid dependency conflicts with Airflow (ADR 0004)
USER root
RUN python -m venv /opt/dbt-venv \
    && /opt/dbt-venv/bin/pip install --no-cache-dir dbt-core==1.12.6 dbt-postgres==1.11.0 \
    && chown -R airflow:0 /opt/dbt-venv

# The ingestion package goes into Airflow's environment; pin Airflow so pip never upgrades it
USER airflow
COPY --chown=airflow:0 pyproject.toml README.md /opt/findata/
COPY --chown=airflow:0 src /opt/findata/src
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" /opt/findata
