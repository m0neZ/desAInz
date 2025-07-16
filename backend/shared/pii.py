"""Utilities for purging personally identifiable information."""

from __future__ import annotations

import re

from sqlalchemy.ext.asyncio import AsyncSession

from .db.models import Idea


_EMAIL_RE = re.compile(r"[\w.-]+@[\w.-]+")
_PHONE_RE = re.compile(r"\+?\d?[\d\s-]{7,}")


def purge_text(text: str) -> str:
    """Return the text with common PII patterns removed."""
    text = _EMAIL_RE.sub("[REDACTED]", text)
    text = _PHONE_RE.sub("[REDACTED]", text)
    return text


async def purge_idea_pii(session: AsyncSession, idea_id: int) -> None:
    """Scrub PII from the specified idea record."""
    idea = await session.get(Idea, idea_id)
    if idea is None:
        return
    idea.title = purge_text(idea.title)
    idea.description = purge_text(idea.description)
    await session.commit()
