"""Notification helpers for publisher errors."""

from __future__ import annotations

import logging
import os
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .db import create_webhook_event

import requests


logger = logging.getLogger(__name__)


def notify_failure(task_id: int, marketplace: str) -> None:
    """Send Slack and PagerDuty alerts about a failed publish task."""
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    payload: dict[str, Any] = {
        "text": f"Publish task {task_id} failed for {marketplace}",
    }
    if webhook:
        try:
            requests.post(webhook, json=payload, timeout=5)
        except requests.RequestException as exc:  # pragma: no cover - best effort
            logger.warning("notification failed: %s", exc)

    try:  # Import lazily so monitoring is optional
        from monitoring.pagerduty import notify_listing_issue
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.debug("pagerduty unavailable: %s", exc)
    else:
        try:
            notify_listing_issue(task_id, "failed")
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("pagerduty notification failed: %s", exc)


async def record_webhook(session: AsyncSession, task_id: int, status: str) -> None:
    """Store webhook event and update the task status."""
    await create_webhook_event(session, task_id, status)
