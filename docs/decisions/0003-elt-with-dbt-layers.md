# ADR 0003 — ELT with layered dbt models

**Status:** accepted

## Context
Transformations must be versioned, tested and documented, and analysts should be able to read them.

## Decision
- Python only **extracts and loads** raw data (no business logic in the loader).
- All transformations are SQL in dbt, organised in `staging → intermediate → marts`.
- Custom schemas are used as-is (`staging`, `intermediate`, `marts`) via an overridden `generate_schema_name` macro, so BI tools see clean schema names.
- Every model has a YAML description; keys and ranges are covered by tests.

## Consequences
- Raw data can always be re-modelled without re-ingesting.
- `dbt build` gives one command that runs models and tests in dependency order; a failed test stops downstream models.
- No external dbt packages are used, so the build works offline; two small generic tests are implemented in `dbt/macros/tests.sql`.
