"""Mockup generation module."""

from __future__ import annotations

from typing import Any, List


def generate_mockups(scored: List[dict[str, Any]]) -> List[dict[str, Any]]:
    """Generate mockups from scored signals.

    Parameters
    ----------
    scored:
        Scored signals.

    Returns
    -------
    list[dict[str, Any]]
        Signals with ``mockup`` field appended.
    """
    result = []
    for item in scored:
        mockup = f"mockup-for-{item.get('id')}"
        result.append({**item, "mockup": mockup})
    return result
