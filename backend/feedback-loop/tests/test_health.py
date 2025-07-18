"""Tests for feedback loop health endpoints."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from feedback_loop.main import app  # noqa: E402

client = TestClient(app)


def test_health_ready() -> None:
    """Health and readiness endpoints return status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}
