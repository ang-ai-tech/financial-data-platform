"""Warehouse connection and schema bootstrap."""

from __future__ import annotations

import os
from importlib import resources

import psycopg


def connect(dsn: str | None = None) -> psycopg.Connection:
    """Connect using WAREHOUSE_DSN, or the standard libpq variables (PGHOST, PGUSER, ...)."""
    return psycopg.connect(dsn or os.environ.get("WAREHOUSE_DSN", ""))


def init_schema(conn: psycopg.Connection) -> None:
    ddl = resources.files("findata").joinpath("sql/schema.sql").read_text(encoding="utf-8")
    conn.execute(ddl)
    conn.commit()
