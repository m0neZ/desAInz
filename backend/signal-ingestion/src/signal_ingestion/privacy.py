"""Utilities for purging personally identifiable information."""

from __future__ import annotations

import re
from typing import Any

# Regex patterns for basic PII detection
#
# These patterns intentionally remain simple and do not aim to be
# exhaustive. They cover the most common formats for PII found in
# analytics payloads without incurring a noticeable performance hit.
PII_PATTERNS = [
    # Email addresses
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    # US phone numbers
    re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    # Simple street addresses (e.g. "123 Main St")
    re.compile(
        r"\b\d{1,5}\s+(?:[A-Za-z0-9.-]+\s)+(?:Street|St|Avenue|Ave|Road|Rd|"
        r"Boulevard|Blvd|Lane|Ln)\b",
        re.IGNORECASE,
    ),
    # Credit card numbers (13 to 16 digits allowing separators)
    re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    # Two capitalized words that could represent a name
    re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b"),
]


def purge_text(text: str) -> str:
    """
    Remove PII substrings from ``text``.

    Parameters
    ----------
    text:
        Arbitrary text that may contain personally identifiable information.

    Returns
    -------
    str
        The sanitized text with all detected PII replaced by ``[REDACTED]``.
    """
    result = text
    for pattern in PII_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


def purge_row(row: dict[str, Any]) -> dict[str, Any]:
    """
    Return a copy of ``row`` with any PII removed.

    Parameters
    ----------
    row:
        Mapping of column names to values from which PII should be stripped.

    Returns
    -------
    dict[str, Any]
        A new dictionary with all string values sanitized.
    """
    return {k: purge_text(v) if isinstance(v, str) else v for k, v in row.items()}


async def purge_pii_rows(limit: int | None = None) -> int:
    """
    Remove PII from stored signals.

    The function opens a database session using :mod:`signal_ingestion.database`
    and applies :func:`purge_pii` from :mod:`signal_ingestion.purge_pii`.

    Parameters
    ----------
    limit:
        Optional maximum number of rows to process.

    Returns
    -------
    int
        The number of rows that were sanitized.
    """
    from . import database
    from .purge_pii import purge_pii

    async with database.SessionLocal() as session:
        return await purge_pii(session, limit)  # type: ignore[no-any-return]
