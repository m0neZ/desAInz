"""Tests for scoring calculations."""

# mypy: ignore-errors

from datetime import UTC, datetime

import numpy as np

from scoring_engine.scoring import Signal, calculate_score, compute_novelty
from scoring_engine.weight_repository import update_weights
from scoring_engine.centroid_job import compute_and_store_centroids
from backend.shared.db import session_scope
from backend.shared.db.models import Embedding


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
        source="src",
        timestamp=datetime.utcnow().replace(tzinfo=UTC),
        engagement_rate=1.0,
        embedding=[1.0, 0.0],
        metadata={"a": 1.0, "b": 0.0},
    )
    score = calculate_score(
        signal,
        median_engagement=1.0,
        topics=["t"],
    )
    assert isinstance(score, float)


def test_scoring_uses_db_centroid(tmp_path) -> None:
    """Novelty uses centroid stored in the database."""
    update_weights(
        freshness=0.0,
        engagement=0.0,
        novelty=1.0,
        community_fit=0.0,
        seasonality=0.0,
    )
    with session_scope() as session:
        dim_vec1 = [1.0] + [0.0] * 767
        dim_vec2 = [0.0] * 767 + [1.0]
        session.add_all(
            [
                Embedding(source="src", embedding=dim_vec1),
                Embedding(source="src", embedding=dim_vec2),
            ]
        )
        session.flush()
    compute_and_store_centroids()
    signal = Signal(
        source="src",
        timestamp=datetime.utcnow().replace(tzinfo=UTC),
        engagement_rate=0.0,
        embedding=dim_vec1,
        metadata={},
    )
    score = calculate_score(signal, median_engagement=0.0, topics=[])
    expected = compute_novelty(
        np.array(dim_vec1), np.array([0.5] + [0.0] * 766 + [0.5])
    )
    assert score == expected
