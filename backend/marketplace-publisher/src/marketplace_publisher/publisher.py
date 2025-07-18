"""Main publishing logic with retry support."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import logging

from requests import RequestException
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .clients import (
    AmazonMerchClient,
    EtsyClient,
    RedbubbleClient,
    Society6Client,
    SeleniumFallback,
)
from .trademark import is_trademarked
from .notifications import notify_failure
from .db import (
    Marketplace,
    PublishStatus,
    PublishTask,
    increment_attempts,
    update_task_status,
)


CLIENTS = {
    Marketplace.redbubble: RedbubbleClient(),
    Marketplace.amazon_merch: AmazonMerchClient(),
    Marketplace.etsy: EtsyClient(),
    Marketplace.society6: Society6Client(),
}

_fallback = SeleniumFallback()

logger = logging.getLogger(__name__)


async def publish_with_retry(
    session: AsyncSession,
    task_id: int,
    marketplace: Marketplace,
    design_path: Path,
    metadata: dict[str, Any],
    max_attempts: int = 3,
) -> bool:
    """
    Publish a design, retrying on failure.

    Return ``True`` when the publish succeeded.
    """
    try:
        await update_task_status(session, task_id, PublishStatus.in_progress)
        title = str(metadata.get("title", ""))
        if title and is_trademarked(title):
            await update_task_status(session, task_id, PublishStatus.failed)
            notify_failure(task_id, marketplace.value)
            return

        client = CLIENTS[marketplace]
        client.publish_design(design_path, metadata)
        await update_task_status(session, task_id, PublishStatus.success)
        return True
    except (RequestException, SQLAlchemyError, RuntimeError) as exc:
        logger.exception(
            "Publish attempt %s for %s failed", task_id, marketplace.value, exc_info=exc
        )
        await increment_attempts(session, task_id)
        await update_task_status(session, task_id, PublishStatus.failed)
        # Retrieve attempts to decide on fallback
        result = await session.execute(
            select(PublishTask.attempts).where(PublishTask.id == task_id)
        )
        attempts = result.scalar_one()
        if attempts >= max_attempts:
            notify_failure(task_id, marketplace.value)
        return False
