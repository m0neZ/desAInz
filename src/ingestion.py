"""Data ingestion module."""

from __future__ import annotations

from typing import Any, List

import requests


def fetch_signals(url: str) -> List[dict[str, Any]]:
    """Fetch trending design signals from ``url``.

    Parameters
    ----------
    url:
        Endpoint returning JSON data.

    Returns
    -------
    list[dict[str, Any]]
        Parsed list of signals.
    """
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    return [data] if isinstance(data, dict) else data
