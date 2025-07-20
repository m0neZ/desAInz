"""Tests for trending keywords endpoint."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402
sys.path.append(
    str(Path(__file__).resolve().parents[2] / "signal-ingestion" / "src")
)  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
import pytest  # noqa: E402

import api_gateway.main as main_module  # noqa: E402
import api_gateway.routes as routes  # noqa: E402

client = TestClient(main_module.app)


def test_trending_keywords(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return mocked popular keywords."""
    monkeypatch.setattr(routes, "get_trending", lambda limit=10: ["foo", "bar"])
    resp = client.get("/trending?limit=2")
    assert resp.status_code == 200
    assert resp.json() == ["foo", "bar"]


def test_trending_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return empty list when no keywords available."""
    monkeypatch.setattr(routes, "get_trending", lambda limit=10: [])
    resp = client.get("/trending")
    assert resp.status_code == 200
    assert resp.json() == []
