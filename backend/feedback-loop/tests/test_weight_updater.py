"""Tests for weight updater."""

from pathlib import Path
from typing import Any
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT.parent))  # noqa: E402
sys.path.append(str(ROOT / "feedback-loop"))  # noqa: E402

from feedback_loop import update_weights  # noqa: E402


def test_update_weights(requests_mock: Any) -> None:
    """Payload should contain aggregated CTR and conversion rate."""
    url = "http://example.com"
    requests_mock.put(f"{url}/weights", json={})
    metrics = [
        {"clicks": 10, "impressions": 100, "purchases": 5},
        {"clicks": 5, "impressions": 50, "purchases": 2},
    ]
    weights = update_weights(url, metrics)
    assert requests_mock.called
    assert requests_mock.request_history[0].json() == weights
    assert weights["engagement"] == 0.1
    assert round(weights["community_fit"], 2) == 0.35
