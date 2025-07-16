"""Notification helpers for publishing failures."""

from __future__ import annotations

import logging
import os
from email.message import EmailMessage
from pathlib import Path
import smtplib

import requests  # type: ignore

from .db import Marketplace

logger = logging.getLogger(__name__)


def _send_slack(message: str) -> None:
    """Send a Slack message using the configured webhook."""
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        logger.warning("SLACK_WEBHOOK_URL not configured")
        return
    try:
        requests.post(webhook, json={"text": message}, timeout=5).raise_for_status()
    except Exception as exc:  # pragma: no cover
        logger.error("failed to send slack notification: %s", exc)


def _send_email(message: str) -> None:
    """Send an email using SMTP configuration."""
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "25"))
    to_addr = os.getenv("NOTIFY_EMAIL_TO")
    from_addr = os.getenv("NOTIFY_EMAIL_FROM")
    if not (host and to_addr and from_addr):
        logger.warning("email notification not configured")
        return
    email = EmailMessage()
    email["Subject"] = "Publishing task failed"
    email["From"] = from_addr
    email["To"] = to_addr
    email.set_content(message)
    try:
        with smtplib.SMTP(host, port) as smtp:
            smtp.send_message(email)
    except Exception as exc:  # pragma: no cover
        logger.error("failed to send email notification: %s", exc)


def notify_failure(task_id: int, marketplace: Marketplace, design_path: Path) -> None:
    """Notify when a publishing task fails after retries."""
    message = (
        "Publishing task "
        f"{task_id} for {marketplace.value} failed for design {design_path}"
    )
    if os.getenv("SLACK_WEBHOOK_URL"):
        _send_slack(message)
    else:
        _send_email(message)
