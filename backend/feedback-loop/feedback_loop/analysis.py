"""Utilities for analysing design performance."""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def highlight_low_performing(
    df: pd.DataFrame, engagement_threshold: float = 0.1
) -> list[int]:
    """Return IDs of designs with engagement below the threshold."""
    if "design_id" not in df.columns or "engagement_rate" not in df.columns:
        logger.debug("missing required columns in metrics frame")
        return []
    low_df = df[df["engagement_rate"] < engagement_threshold]
    return list(low_df["design_id"].astype(int).tolist())
