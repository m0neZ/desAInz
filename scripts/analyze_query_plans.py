#!/usr/bin/env python
"""Analyze query plans and suggest missing indexes."""

from __future__ import annotations

import logging
import os

import psycopg2
from psycopg2.extras import DictCursor

QUERIES = [
    ("signals_by_idea", "SELECT * FROM signals WHERE idea_id = %s LIMIT 1", (1,)),
    (
        "mockups_by_idea",
        "SELECT * FROM mockups WHERE idea_id = %s LIMIT 1",
        (1,),
    ),
    (
        "listings_by_mockup",
        "SELECT * FROM listings WHERE mockup_id = %s LIMIT 1",
        (1,),
    ),
]


def main() -> None:
    """Run EXPLAIN on common queries and print query plans."""
    dsn = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/app",
    )
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            for name, query, params in QUERIES:
                cur.execute("EXPLAIN " + query, params)
                plan = "\n".join(row[0] for row in cur.fetchall())
                logging.info("%s:\n%s", name, plan)
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
