-- Raw layer: data as delivered by the sources, plus load metadata.
-- Idempotent: safe to run on every pipeline start.

create schema if not exists raw;

create table if not exists raw.ecb_exchange_rates (
    currency    char(3)        not null,
    rate_date   date           not null,
    rate        numeric(18, 6) not null,  -- units of currency per 1 EUR
    _batch_id   text           not null,
    _loaded_at  timestamptz    not null default now(),
    primary key (currency, rate_date)
);

create table if not exists raw.fred_observations (
    series_id         text           not null,
    observation_date  date           not null,
    value             numeric(18, 6) not null,
    _batch_id         text           not null,
    _loaded_at        timestamptz    not null default now(),
    primary key (series_id, observation_date)
);

-- Curated metadata from config/sources.yml (see ADR 0002)
create table if not exists raw.fred_series (
    series_id    text        primary key,
    series_name  text        not null,
    units        text        not null,
    frequency    text        not null,
    category     text        not null,
    _loaded_at   timestamptz not null default now()
);

-- One row per source per run: what was loaded, when, and whether it worked
create table if not exists raw.ingestion_log (
    batch_id       text        not null,
    source         text        not null,
    start_date     date,
    started_at     timestamptz not null default now(),
    finished_at    timestamptz,
    rows_loaded    integer,
    status         text        not null check (status in ('running', 'success', 'failed')),
    error_message  text,
    primary key (batch_id, source)
);
