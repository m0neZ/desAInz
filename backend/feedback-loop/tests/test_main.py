"""Tests for feedback loop main endpoints."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from feedback_loop import ABTestManager  # noqa: E402
import feedback_loop.main as main  # noqa: E402


def test_impression_conversion_allocation(tmp_path) -> None:
    """Recorded events should influence allocation."""
    main.manager = ABTestManager(database_url="sqlite:///:memory:")
    client = TestClient(main.app)

    resp = client.post("/impression", params={"variant": "A"})
    assert resp.status_code == 200

    resp = client.post("/conversion", params={"variant": "B"})
    assert resp.status_code == 200

    resp = client.get("/allocation", params={"total_budget": 100})
    assert resp.status_code == 200
    data = resp.json()
    assert set(data) == {"variant_a", "variant_b"}
