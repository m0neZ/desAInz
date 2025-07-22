"""Tests for continuous aggregate creation on startup."""

from __future__ import annotations

import warnings
import pytest
from fastapi.testclient import TestClient
from typing import Any

warnings.filterwarnings("ignore", category=DeprecationWarning)

from backend.optimization import api as opt_api
from backend.optimization.storage import MetricsStore


def test_materialized_view_created(postgresql: Any) -> None:
    """Ensure the hourly aggregate view exists after startup."""
    url = postgresql.info.dsn
    opt_api.store = MetricsStore(url)
    with TestClient(opt_api.app):
        pass
    with postgresql.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_matviews WHERE matviewname='metrics_hourly'")
        assert cur.fetchone() is not None
