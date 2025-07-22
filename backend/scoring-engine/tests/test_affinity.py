"""Tests for affinity utilities."""

# mypy: ignore-errors

from __future__ import annotations

import math

import numpy as np

from scoring_engine.affinity import (
    DIMENSION,
    hashtag_embedding,
    metadata_embedding,
    subreddit_embedding,
)
from scoring_engine.scoring import compute_community_fit


def test_subreddit_embedding_deterministic() -> None:
    """Subreddit embeddings should be deterministic."""
    v1 = subreddit_embedding("Python")
    v2 = subreddit_embedding("python")
    assert np.array_equal(v1, v2)


def test_metadata_embedding_weighted_average() -> None:
    """metadata_embedding returns weighted average of components."""
    meta = {"r/foo": 2.0, "#bar": 1.0}
    expected = (subreddit_embedding("foo") * 2.0 + hashtag_embedding("bar")) / 3.0
    result = metadata_embedding(tuple(sorted(meta.items())))
    assert np.allclose(result, expected)


def test_compute_community_fit_uses_embeddings() -> None:
    """compute_community_fit scales embedding norm."""
    meta = {"r/foo": 1.0}
    vec = subreddit_embedding("foo")
    expected = np.linalg.norm(vec) / math.sqrt(DIMENSION)
    result = compute_community_fit(meta)
    assert result == expected
