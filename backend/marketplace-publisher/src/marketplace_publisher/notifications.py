"""Notification helpers for publisher errors."""

from __future__ import annotations

import logging
import os
from typing import Any

import requests


logger = logging.getLogger(__name__)


def notify_failure(task_id: int, marketplace: str) -> None:
    """Send a Slack notification about a failed publish task."""
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        return
    payload: dict[str, Any] = {
        "text": f"Publish task {task_id} failed for {marketplace}",
    }
    try:
        requests.post(webhook, json=payload, timeout=5)
    except requests.RequestException as exc:  # pragma: no cover - best effort
        logger.warning("notification failed: %s", exc)
