"""Tests for continuous aggregate creation on startup."""

from __future__ import annotations

import warnings
import psycopg2
import pytest
from fastapi.testclient import TestClient

warnings.filterwarnings("ignore", category=DeprecationWarning)

from backend.optimization import api as opt_api
from backend.optimization.storage import MetricsStore


def test_materialized_view_created(postgresql: psycopg2.extensions.connection) -> None:
    """Ensure the hourly aggregate view exists after startup."""
    opt_api.store = MetricsStore(postgresql.info.dsn)
    with TestClient(opt_api.app):
        pass
    with psycopg2.connect(postgresql.info.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_matviews WHERE matviewname='metrics_hourly'")
            assert cur.fetchone() is not None
