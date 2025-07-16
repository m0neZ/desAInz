"""Tests for notification functionality."""

import pytest

from marketplace_publisher.publisher import notify_failure
from marketplace_publisher.db import Marketplace


@pytest.mark.asyncio
async def test_notify_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    called: bool = False

    async def fake_post(url: str, json: dict[str, str], timeout: int) -> None:
        nonlocal called
        called = True

    monkeypatch.setenv("SLACK_WEBHOOK_URL", "http://example.com")
    monkeypatch.setattr("marketplace_publisher.publisher.requests.post", fake_post)
    await notify_failure(1, Marketplace.redbubble, 2)
    assert called
