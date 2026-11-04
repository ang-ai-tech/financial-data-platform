# ADR 0002 — FRED graph CSV endpoint instead of the FRED API

**Status:** accepted

## Context
The official FRED API requires a (free) personal API key. Anyone cloning the repository would need to register before running anything.

## Options considered
- **FRED API** (`api.stlouisfed.org`) — returns metadata (title, units) and supports vintages, but needs a key.
- **Graph CSV endpoint** (`fred.stlouisfed.org/graph/fredgraph.csv?id=...`) — public, no key, returns `observation_date,<SERIES_ID>`.

## Decision
Use the CSV endpoint. Series metadata (name, units, frequency, category) is declared in `config/sources.yml` and loaded into `raw.fred_series`.

## Consequences
- The project runs end-to-end with zero registration (NFR-2).
- Metadata is curated by hand — acceptable for a small, deliberate list of series.
- Vintage/real-time data is not available; revisions are handled by the 120-day look-back window instead.
- The extractor is isolated in `findata/extract/fred.py`, so switching to the API is a local change.

Only public-domain series from US government agencies (BLS, Federal Reserve, US Treasury) are used.
