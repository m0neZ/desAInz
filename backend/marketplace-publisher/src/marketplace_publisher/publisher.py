"""Main publishing logic with retry support."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .clients import AmazonMerchClient, EtsyClient, RedbubbleClient, SeleniumFallback
from .trademark import TrademarkError, verify_no_trademark_issue
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
}

_fallback = SeleniumFallback()


async def publish_with_retry(
    session: AsyncSession,
    task_id: int,
    marketplace: Marketplace,
    design_path: Path,
    metadata: dict[str, Any],
    max_attempts: int = 3,
) -> None:
    """Publish a design, retrying on failure."""
    try:
        await update_task_status(session, task_id, PublishStatus.in_progress)
        await verify_no_trademark_issue(metadata.get("title", ""))
        client = CLIENTS[marketplace]
        client.publish_design(design_path, metadata)
        await update_task_status(session, task_id, PublishStatus.success)
    except TrademarkError:
        await update_task_status(session, task_id, PublishStatus.failed)
    except Exception:  # pylint: disable=broad-except
        await increment_attempts(session, task_id)
        await update_task_status(session, task_id, PublishStatus.failed)
        # Retrieve attempts to decide on fallback
        result = await session.execute(
            select(PublishTask.attempts).where(PublishTask.id == task_id)
        )
        attempts = result.scalar_one()
        if attempts < max_attempts:
            _fallback.publish(marketplace, design_path, metadata)
            await update_task_status(session, task_id, PublishStatus.success)
        else:
            await update_task_status(session, task_id, PublishStatus.failed)
