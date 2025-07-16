"""Tests for weight updater."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from feedback_loop import update_weights


def test_update_weights(requests_mock) -> None:
    """Update endpoint should receive provided weights."""
    url = "http://example.com"
    requests_mock.put(f"{url}/weights", json={})
    update_weights(url, {"freshness": 1.0})
    assert requests_mock.called
    assert requests_mock.request_history[0].json() == {"freshness": 1.0}
