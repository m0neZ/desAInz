"""Tests for PagerDuty utility functions."""

from __future__ import annotations
from pathlib import Path
import sys
from typing import Any

# Add monitoring src to path
sys.path.append(
    str(Path(__file__).resolve().parents[1] / "backend" / "monitoring" / "src")
)

from monitoring import pagerduty  # noqa: E402


PAGERDUTY_URL = pagerduty.PAGERDUTY_URL


def test_trigger_sla_violation_sends_request(
    requests_mock: Any, monkeypatch: Any
) -> None:
    """trigger_sla_violation should POST alert when routing key present."""
    monkeypatch.setenv("PAGERDUTY_ROUTING_KEY", "key")
    requests_mock.post(PAGERDUTY_URL, status_code=202)
    pagerduty.trigger_sla_violation(2.5)
    assert requests_mock.called
    history = requests_mock.request_history[0]
    assert history.json()["routing_key"] == "key"
    assert "2.50" in history.json()["payload"]["summary"]


def test_notify_listing_issue_sends_request(
    requests_mock: Any, monkeypatch: Any
) -> None:
    """notify_listing_issue should POST listing alert when routing key present."""
    monkeypatch.setenv("PAGERDUTY_ROUTING_KEY", "key")
    requests_mock.post(PAGERDUTY_URL, status_code=202)
    pagerduty.notify_listing_issue(123, "removed")
    assert requests_mock.called
    history = requests_mock.request_history[0]
    assert history.json()["payload"]["summary"] == "Listing 123 is removed"


def test_pagerduty_disabled_skips_request(requests_mock: Any, monkeypatch: Any) -> None:
    """No request should be made when ENABLE_PAGERDUTY is false."""
    monkeypatch.setenv("PAGERDUTY_ROUTING_KEY", "key")
    from monitoring import settings as monitoring_settings

    monkeypatch.setattr(monitoring_settings.settings, "enable_pagerduty", False)
    requests_mock.post(PAGERDUTY_URL, status_code=202)
    pagerduty.trigger_sla_violation(1.0)
    assert not requests_mock.called
