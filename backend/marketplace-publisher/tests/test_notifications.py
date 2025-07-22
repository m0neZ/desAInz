"""Tests for notification helpers."""  # noqa: E402

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

import asyncio
import logging

import pytest
import responses
import requests
import backend.shared.http as http

from marketplace_publisher import notifications  # noqa: E402
from monitoring import pagerduty  # noqa: E402


@pytest.mark.asyncio()  # type: ignore[misc]
async def test_notify_failure_sends_discord_and_pagerduty(monkeypatch: Any) -> None:
    """notify_failure should POST to Discord and trigger PagerDuty."""
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
    monkeypatch.setattr(
        http,
        "request_with_retry",
        lambda *a, **kw: fake_post(a[1], kw.get("json"), kw.get("timeout")),
    )
    monkeypatch.setattr(pagerduty, "notify_listing_issue", fake_pd)
    monkeypatch.setattr(asyncio, "to_thread", lambda func, *a, **kw: func(*a, **kw))

    notifications.notify_failure(7, "etsy")
    await asyncio.sleep(0)

    assert sent["url"] == "http://slack"
    assert "7" in sent["json"]["text"]
    assert pd_calls == [(7, "failed")]


@pytest.mark.asyncio()  # type: ignore[misc]
async def test_notify_failure_handles_timeout(
    monkeypatch: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Timeouts should be logged without raising exceptions."""
    pd_calls: list[tuple[int, str]] = []

    def fake_pd(listing_id: int, state: str) -> None:
        pd_calls.append((listing_id, state))

    caplog.set_level(logging.WARNING)

    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, "http://slack", body=requests.Timeout())
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "http://slack")
        monkeypatch.setattr(pagerduty, "notify_listing_issue", fake_pd)
        monkeypatch.setattr(asyncio, "to_thread", lambda func, *a, **kw: func(*a, **kw))
        notifications.notify_failure(9, "etsy")
        await asyncio.sleep(0)

    assert pd_calls == [(9, "failed")]
    assert "notification failed" in caplog.text


@pytest.mark.asyncio()  # type: ignore[misc]
async def test_notify_failure_pagerduty_timeout(
    monkeypatch: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Handle PagerDuty timeouts gracefully."""
    caplog.set_level(logging.WARNING)

    def boom(*args: Any, **kwargs: Any) -> None:
        raise requests.Timeout()

    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, "http://slack", json={})
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "http://slack")
        monkeypatch.setattr(pagerduty, "notify_listing_issue", boom)
        monkeypatch.setattr(asyncio, "to_thread", lambda func, *a, **kw: func(*a, **kw))
        notifications.notify_failure(11, "etsy")
        await asyncio.sleep(0)

    assert "pagerduty notification failed" in caplog.text
