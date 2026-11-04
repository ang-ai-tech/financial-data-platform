.PHONY: up down reset logs test lint sample-load dbt-build

up:            ## Build images and start the stack
	docker compose up -d --build

down:          ## Stop the stack (data is kept)
	docker compose down

reset:         ## Stop the stack and delete the warehouse volume
	docker compose down -v

logs:
	docker compose logs -f airflow

test:          ## Unit tests (no database needed)
	pytest

lint:
	ruff check .

sample-load:   ## Load the bundled CSV snapshot instead of calling the APIs
	docker compose exec airflow findata load-sample --dir /opt/findata-sample

dbt-build:     ## Run dbt models and tests inside the Airflow container
	docker compose exec airflow bash -c "cd /opt/airflow/dbt && /opt/dbt-venv/bin/dbt build --profiles-dir ."
