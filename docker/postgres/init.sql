-- Runs once, on the first start of an empty volume.
-- The `warehouse` database is created by POSTGRES_DB; Airflow gets its own metadata database.
create database airflow;
