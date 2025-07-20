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
import os
from typing import Iterable

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
    dsn = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/app")
    limit = int(os.getenv("SLOW_QUERY_LIMIT", str(DEFAULT_LIMIT)))
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
