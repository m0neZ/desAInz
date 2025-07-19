from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure local packages can be imported
ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))
# Add monitoring src to path
sys.path.append(str(ROOT / "backend" / "monitoring" / "src"))

import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from marketplace_publisher import notifications  # noqa: E402
from monitoring import pagerduty  # noqa: E402


def test_notify_failure_sends_slack_and_pagerduty(monkeypatch: Any) -> None:
    """notify_failure should POST to Slack and trigger PagerDuty."""
    sent: dict[str, Any] = {}

    def fake_post(url: str, json: Any, timeout: int) -> None:  # noqa: D401
        sent["url"] = url
        sent["json"] = json
        sent["timeout"] = timeout

    pd_calls: list[tuple[int, str]] = []

    def fake_pd(listing_id: int, state: str) -> None:  # noqa: D401
        pd_calls.append((listing_id, state))

    monkeypatch.setenv("SLACK_WEBHOOK_URL", "http://slack")
    monkeypatch.setenv("PAGERDUTY_ROUTING_KEY", "key")
    monkeypatch.setattr(notifications.requests, "post", fake_post)
    monkeypatch.setattr(pagerduty, "notify_listing_issue", fake_pd)

    notifications.notify_failure(7, "etsy")

    assert sent["url"] == "http://slack"
    assert "7" in sent["json"]["text"]
    assert pd_calls == [(7, "failed")]
