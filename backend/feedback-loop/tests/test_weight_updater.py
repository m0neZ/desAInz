"""Tests for weight updater."""

from pathlib import Path
from typing import Any
import sys
import importlib.util
import pytest
from requests import RequestException

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT.parent))
sys.path.append(str(ROOT / "feedback-loop"))


WEIGHT_UPDATER = ROOT / "feedback-loop" / "feedback_loop" / "weight_updater.py"
spec = importlib.util.spec_from_file_location("weight_updater", WEIGHT_UPDATER)
weight_updater = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(weight_updater)

update_weights = weight_updater.update_weights


def test_update_weights(requests_mock: Any) -> None:
    """Payload should contain aggregated CTR and conversion rate."""
    url = "http://example.com"
    requests_mock.post(f"{url}/weights/feedback", json={})
    metrics = [
        {"clicks": 10, "impressions": 100, "purchases": 5},
        {"clicks": 5, "impressions": 50, "purchases": 2},
    ]
    weights = update_weights(url, metrics)
    assert requests_mock.called
    assert requests_mock.request_history[0].json() == weights
    assert weights["engagement"] == 0.1
    assert round(weights["community_fit"], 2) == 0.47


def test_update_weights_error(requests_mock: Any) -> None:
    """The function should raise for non-2xx responses."""
    url = "http://example.com"
    requests_mock.post(f"{url}/weights/feedback", status_code=500)
    with pytest.raises(RequestException):
        update_weights(url, [{"ctr": 0.1, "conversion_rate": 0.2}])


def test_update_weights_retries(requests_mock: Any) -> None:
    """The function should retry on temporary errors."""
    url = "http://example.com"
    requests_mock.post(
        f"{url}/weights/feedback",
        [{"status_code": 500}, {"json": {}}],
    )
    metrics = [{"ctr": 0.1, "conversion_rate": 0.2}]
    update_weights(url, metrics)
    assert requests_mock.call_count == 2
