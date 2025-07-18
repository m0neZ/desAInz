"""Scoring algorithms."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Iterable

import numpy as np
from sklearn.preprocessing import StandardScaler

from .weight_repository import get_centroid, get_weights


class Signal:
    """Simple representation of an idea signal."""

    def __init__(
        self,
        source: str,
        timestamp: datetime,
        engagement_rate: float,
        embedding: Iterable[float],
        metadata: dict[str, float],
    ) -> None:
        """Create a new signal instance."""
        self.source = source
        self.timestamp = timestamp
        self.engagement_rate = engagement_rate
        self.embedding = np.array(list(embedding), dtype=float)
        self.metadata = metadata


_SCALER = StandardScaler()


def compute_freshness(timestamp: datetime) -> float:
    """Return freshness score based on time decay in hours."""
    hours = (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600
    return 1 / (1 + math.exp(hours / 24))


def compute_engagement(current: float, median: float) -> float:
    """Z-score of engagement rate against median."""
    arr = np.array([[current], [median]])
    scaled = _SCALER.fit_transform(arr)
    return float(scaled[0][0])


def compute_novelty(embedding: np.ndarray, centroid: np.ndarray) -> float:
    """One minus cosine similarity to centroid."""
    dot = float(np.dot(embedding, centroid))
    norm = float(np.linalg.norm(embedding) * np.linalg.norm(centroid))
    if norm == 0:
        return 0.0
    return 1 - dot / norm


def compute_community_fit(metadata: dict[str, float]) -> float:
    """Simplistic community affinity from metadata weights."""
    if not metadata:
        return 0.0
    return float(sum(metadata.values()) / len(metadata))


def compute_seasonality(timestamp: datetime, topics: Iterable[str]) -> float:
    """Seasonal boost using month and topic heuristics."""
    month = timestamp.month
    if month in {11, 12}:
        base = 1.2
    elif month in {6, 7, 8}:
        base = 1.1
    else:
        base = 1.0
    return base


def calculate_score(
    signal: Signal,
    median_engagement: float,
    topics: Iterable[str],
) -> float:
    """Calculate composite score using current weights.

    The centroid is automatically fetched based on ``signal.source``.
    """
    weights = get_weights()
    centroid_list = get_centroid(signal.source)
    if centroid_list is None:
        centroid = np.zeros_like(signal.embedding)
    else:
        centroid = np.array(centroid_list, dtype=float)
    freshness = compute_freshness(signal.timestamp)
    engagement = compute_engagement(signal.engagement_rate, median_engagement)
    novelty = compute_novelty(signal.embedding, centroid)
    community_fit = compute_community_fit(signal.metadata)
    seasonality = compute_seasonality(signal.timestamp, topics)
    score = (
        weights.freshness * freshness
        + weights.engagement * engagement
        + weights.novelty * novelty
        + weights.community_fit * community_fit
        + weights.seasonality * seasonality
    )
    return float(score)
