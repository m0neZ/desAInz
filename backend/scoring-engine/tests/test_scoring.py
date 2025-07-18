"""Tests for scoring calculations."""

# mypy: ignore-errors

from datetime import datetime, timezone

import numpy as np

from scoring_engine.scoring import Signal, calculate_score
from scoring_engine.weight_repository import update_weights


def test_calculate_score_simple(tmp_path, monkeypatch):
    """Calculate score using deterministic weights."""
    update_weights(
        freshness=1.0,
        engagement=1.0,
        novelty=1.0,
        community_fit=1.0,
        seasonality=1.0,
    )
    signal = Signal(
        timestamp=datetime.now(timezone.utc),
        engagement_rate=1.0,
        embedding=[1.0, 0.0],
        metadata={"a": 1.0, "b": 0.0},
    )
    centroid = np.array([0.0, 1.0])
    score = calculate_score(
        signal,
        centroid,
        median_engagement=1.0,
        topics=["t"],
    )
    assert isinstance(score, float)
