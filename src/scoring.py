"""Signal scoring module."""

from __future__ import annotations

from typing import Any, List


def score_signals(signals: List[dict[str, Any]]) -> List[dict[str, Any]]:
    """Score signals by length of ``title`` field.

    Parameters
    ----------
    signals:
        Signals to score.

    Returns
    -------
    list[dict[str, Any]]
        Signals with an added ``score`` key.
    """
    scored = []
    for item in signals:
        title = str(item.get("title", ""))
        score = len(title)
        scored.append({**item, "score": score})
    return scored
