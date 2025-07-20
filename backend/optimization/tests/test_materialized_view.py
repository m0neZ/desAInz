"""Tests for continuous aggregate creation on startup."""

from __future__ import annotations

import warnings
import shutil
import psycopg2
import pytest
from fastapi.testclient import TestClient
from testing.postgresql import Postgresql

warnings.filterwarnings("ignore", category=DeprecationWarning)

from backend.optimization import api as opt_api
from backend.optimization.storage import MetricsStore


@pytest.mark.skipif(shutil.which("initdb") is None, reason="initdb not available")
def test_materialized_view_created() -> None:
    """Ensure the hourly aggregate view exists after startup."""
    with Postgresql() as pg:
        url = pg.url()
        opt_api.store = MetricsStore(url)
        with TestClient(opt_api.app):
            pass
        with psycopg2.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_matviews WHERE matviewname='metrics_hourly'"
                )
                assert cur.fetchone() is not None
