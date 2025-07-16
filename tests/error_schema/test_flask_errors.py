"""Verify standardized error responses for Flask service."""

# mypy: ignore-errors

import sys
from pathlib import Path
from flask.testing import FlaskClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "scoring-engine"))
sys.path.insert(0, str(ROOT))
from scoring_engine.app import app

app.config.update(TESTING=True)


def test_internal_error_response(monkeypatch) -> None:
    """Unhandled exceptions should return standardized error."""
    client: FlaskClient = app.test_client()

    def fail(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("scoring_engine.weight_repository.get_weights", fail)
    resp = client.get("/weights")
    assert resp.status_code == 500
    body = resp.get_json()
    assert set(body) == {"error", "trace_id"}
    assert body["error"]
    assert body["trace_id"]
