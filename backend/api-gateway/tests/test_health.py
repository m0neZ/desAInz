"""Tests for health and readiness endpoints."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from api_gateway.main import app  # noqa: E402

client = TestClient(app)


def test_health_ready() -> None:
    """Health and readiness endpoints return expected status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}
