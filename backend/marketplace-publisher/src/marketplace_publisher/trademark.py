"""Trademark search utilities for marketplace publishing."""

from __future__ import annotations

import logging
from typing import Any, cast

import requests

logger = logging.getLogger(__name__)

USPTO_ENDPOINT = "https://developer.uspto.gov/ibd-api/v1/application/publications"
EUIPO_ENDPOINT = "https://api.tmdn.org/tmview/v1/trademarks"


def _query_api(url: str, term: str) -> bool:
    """Return ``True`` if ``term`` matches a trademark at ``url``."""
    try:
        response = requests.get(url, params={"searchText": term}, timeout=10)
        response.raise_for_status()
        data = cast(dict[str, Any], response.json())
    except requests.RequestException as exc:  # pragma: no cover - network errors
        logger.warning("trademark lookup failed: %s", exc)
        return False
    return bool(data.get("totalRows", 0) > 0)


def is_trademarked(term: str) -> bool:
    """Return ``True`` if ``term`` is trademarked in either USPTO or EUIPO."""
    return _query_api(USPTO_ENDPOINT, term) or _query_api(EUIPO_ENDPOINT, term)
