"""Helpers for identifying underperforming designs."""

from __future__ import annotations

import pandas as pd


def highlight_low_performing_designs(
    df: pd.DataFrame,
    metric: str,
    threshold: float,
) -> list[int]:
    """Return IDs of designs where ``metric`` is below ``threshold``."""
    if "design_id" not in df.columns:
        raise ValueError("design_id column missing")
    if metric not in df.columns:
        raise ValueError(f"Metric {metric} not found")
    low = df[df[metric] < threshold]
    return list(low["design_id"].astype(int).tolist())
