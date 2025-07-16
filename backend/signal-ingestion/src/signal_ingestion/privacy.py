"""Utilities for purging personally identifiable information."""

from __future__ import annotations

import re
from typing import Any

# Regex patterns for basic PII detection
PII_PATTERNS = [
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
]


def purge_text(text: str) -> str:
    """Remove PII substrings from ``text``."""
    result = text
    for pattern in PII_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


def purge_row(row: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``row`` with any PII removed."""
    return {k: purge_text(v) if isinstance(v, str) else v for k, v in row.items()}
