"""Notification helpers for publisher errors."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .db import create_webhook_event

import requests
from backend.shared.http import request_with_retry


logger = logging.getLogger(__name__)


async def _dispatch_notifications(task_id: int, marketplace: str) -> None:
    """Send Discord and PagerDuty alerts in the background."""
    payload: dict[str, Any] = {
        "text": f"Publish task {task_id} failed for {marketplace}",
    }
    webhook = os.getenv("SLACK_WEBHOOK_URL")

    async def slack() -> None:
        if not webhook:
            return
        try:
            await asyncio.to_thread(
                request_with_retry, "POST", webhook, json=payload, timeout=2
            )
        except requests.RequestException as exc:  # pragma: no cover - best effort
            logger.warning("notification failed: %s", exc)

    async def pagerduty() -> None:
        try:
            from monitoring.pagerduty import notify_listing_issue
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.debug("pagerduty unavailable: %s", exc)
            return
        try:
            await asyncio.to_thread(notify_listing_issue, task_id, "failed")
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("pagerduty notification failed: %s", exc)

    await asyncio.gather(slack(), pagerduty())


def notify_failure(task_id: int, marketplace: str) -> None:
    """Schedule notifications about a failed publish task."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.warning("no running loop to send notifications")
        return
    loop.create_task(_dispatch_notifications(task_id, marketplace))


async def record_webhook(session: AsyncSession, task_id: int, status: str) -> None:
    """Store webhook event and update the task status."""
    await create_webhook_event(session, task_id, status)
