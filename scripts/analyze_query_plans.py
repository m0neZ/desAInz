#!/usr/bin/env python
"""
Analyze query plans and suggest missing indexes.

This script connects to the database defined by ``DATABASE_URL`` and
inspects ``pg_stat_statements`` for the slowest queries. Each query is then
passed to ``EXPLAIN`` so that the query planner output can be reviewed.
The goal is to identify missing indexes or other optimisations. The
``pg_stat_statements`` extension must be installed for the analysis to work.
"""

from __future__ import annotations

import logging
from typing import Iterable

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

import psycopg2
from psycopg2.extras import DictCursor

SLOW_QUERY_SQL = """
    SELECT query
    FROM pg_stat_statements
    WHERE calls > 0
    ORDER BY mean_exec_time DESC
    LIMIT %s
"""

CHECK_EXTENSION_SQL = "SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'"

DEFAULT_LIMIT = 5


class Settings(BaseSettings):
    """Configuration for database analysis."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    database_url: AnyUrl = Field(
        default=AnyUrl("postgresql://user:password@localhost:5432/app"),
        alias="DATABASE_URL",
    )
    slow_query_limit: int = Field(default=DEFAULT_LIMIT, alias="SLOW_QUERY_LIMIT")


settings = Settings()


def _extension_available(cur: DictCursor) -> bool:
    """Return ``True`` if ``pg_stat_statements`` extension is installed."""
    cur.execute(CHECK_EXTENSION_SQL)
    return cur.fetchone() is not None


def _fetch_slow_queries(cur: DictCursor, limit: int) -> Iterable[str]:
    """Return the ``limit`` slowest queries recorded by ``pg_stat_statements``."""
    cur.execute(SLOW_QUERY_SQL, (limit,))
    rows = cur.fetchall()
    return [row["query"] for row in rows]


def _explain_query(cur: DictCursor, query: str) -> str:
    """Return the ``EXPLAIN`` plan for ``query``."""
    cur.execute("EXPLAIN " + query)
    return "\n".join(row[0] for row in cur.fetchall())


def main() -> None:
    """Print ``EXPLAIN`` plans for the slowest statements."""
    dsn = str(settings.database_url)
    limit = settings.slow_query_limit
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            if not _extension_available(cur):
                logging.error("pg_stat_statements extension is not installed")
                return
            for query in _fetch_slow_queries(cur, limit):
                plan = _explain_query(cur, query)
                logging.info("Query: %s\n%s", query, plan)
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
