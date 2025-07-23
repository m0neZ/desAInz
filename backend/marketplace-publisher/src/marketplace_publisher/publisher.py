"""Main publishing logic with retry support."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Mapping
import logging
import subprocess

from requests import RequestException
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .clients import (
    AmazonMerchClient,
    EtsyClient,
    RedbubbleClient,
    Society6Client,
    ZazzleClient,
    SeleniumFallback,
)
from .trademark import is_trademarked
from .notifications import notify_failure
from mockup_generation.post_processor import ensure_not_nsfw
from PIL import Image
from . import rules
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
    Marketplace.zazzle: ZazzleClient(),
}

_fallback = SeleniumFallback()

logger = logging.getLogger(__name__)


def _invalidate_cdn_cache(path: str) -> None:
    """Invalidate CDN caches for ``path`` if configured."""
    from backend.shared.config import settings as shared_settings

    distribution = shared_settings.cdn_distribution_id
    if not distribution:
        return
    script = Path(__file__).resolve().parents[2] / "scripts" / "invalidate_cache.sh"
    subprocess.run([str(script), distribution, f"/{path}"], check=True)


def validate_mockup(
    marketplace: Marketplace, design_path: Path, metadata: Mapping[str, Any]
) -> str | None:
    """Return reason if ``design_path`` violates marketplace policies."""
    rules.validate_mockup(marketplace, design_path)
    title = str(metadata.get("title", ""))
    if title and is_trademarked(title):
        return "trademarked"
    try:
        with Image.open(design_path) as img:
            ensure_not_nsfw(img)
    except ValueError:
        return "nsfw"
    return None


def publish_design(
    marketplace: Marketplace, design_path: Path, metadata: Mapping[str, Any]
) -> str | Literal["trademarked"]:
    """Publish ``design_path`` to ``marketplace`` if allowed."""
    title = str(metadata.get("title", ""))
    if title and is_trademarked(title):
        return "trademarked"
    client = CLIENTS[marketplace]
    return client.publish_design(design_path, dict(metadata))


async def publish_with_retry(
    session: AsyncSession,
    task_id: int,
    marketplace: Marketplace,
    design_path: Path,
    metadata: dict[str, Any],
    max_attempts: int = 3,
) -> str | Literal["nsfw", "trademarked"] | None:
    """
    Publish a design with retry support.

    Return the created listing ID when publishing succeeds. If the design violates
    policy checks, return the failure reason instead.
    """
    try:
        await update_task_status(session, task_id, PublishStatus.in_progress)
        reason = validate_mockup(marketplace, design_path, metadata)
        if reason is not None:
            await update_task_status(session, task_id, PublishStatus.failed)
            notify_failure(task_id, marketplace.value)
            return reason

        listing_id = publish_design(marketplace, design_path, metadata)
        if listing_id == "trademarked":
            await update_task_status(session, task_id, PublishStatus.failed)
            notify_failure(task_id, marketplace.value)
            return "trademarked"
        await update_task_status(session, task_id, PublishStatus.success)
        _invalidate_cdn_cache(design_path.name)
        return listing_id
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
        return None
