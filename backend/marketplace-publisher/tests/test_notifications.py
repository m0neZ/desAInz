"""Tests for publisher notification helpers."""

from pathlib import Path

import pytest

from marketplace_publisher.db import Marketplace
from marketplace_publisher.notifications import notify_failure


@pytest.mark.parametrize("use_slack", [True, False])
def test_notify_failure(monkeypatch, use_slack: bool) -> None:
    """Verify that notifications are sent via Slack or email."""
    called = {}

    if use_slack:
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "http://example.com")
    else:
        monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
        monkeypatch.setenv("SMTP_HOST", "localhost")
        monkeypatch.setenv("SMTP_PORT", "25")
        monkeypatch.setenv("NOTIFY_EMAIL_FROM", "a@b.com")
        monkeypatch.setenv("NOTIFY_EMAIL_TO", "c@d.com")

    def fake_post(url, json, timeout):  # type: ignore[unused-argument]
        called["slack"] = url

        class Resp:
            def raise_for_status(self) -> None:  # noqa: D401
                """No-op."""
                return None

        return Resp()

    class DummySMTP:
        def __init__(self, host: str, port: int) -> None:  # noqa: D401
            called["smtp"] = f"{host}:{port}"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def send_message(self, _msg):
            called["sent"] = True

    if use_slack:
        monkeypatch.setattr(
            "marketplace_publisher.notifications.requests.post",
            fake_post,
        )
    else:
        monkeypatch.setattr(
            "marketplace_publisher.notifications.smtplib.SMTP",
            DummySMTP,
        )

    notify_failure(1, Marketplace.redbubble, Path("d.png"))

    assert called
