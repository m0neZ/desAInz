"""Repository for weight access."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from sqlalchemy import select

from backend.shared.db import engine, session_scope
from backend.shared.db.models import Weights
from backend.shared.db.base import Base


# Weight update smoothing factor for feedback adjustments
FEEDBACK_SMOOTHING = 0.1

# JSON file storing the latest persisted weights
WEIGHTS_FILE = Path(__file__).with_name("weights.json")

# Create table if not exists
Base.metadata.create_all(bind=engine)


@dataclass
class WeightParams:
    """Dataclass for weight values."""

    freshness: float
    engagement: float
    novelty: float
    community_fit: float
    seasonality: float


def get_centroid(source: str) -> list[float] | None:
    """Return centroid vector for ``source`` if present."""
    with session_scope() as session:
        weights = session.scalar(select(Weights).where(Weights.source == source))
        if weights is None:
            return None
        return list(weights.centroid) if weights.centroid is not None else None


def upsert_centroid(source: str, centroid: list[float]) -> None:
    """Create or update centroid for ``source``."""
    with session_scope() as session:
        weights = session.scalar(select(Weights).where(Weights.source == source))
        if weights is None:
            weights = Weights(source=source)
            session.add(weights)
        weights.centroid = centroid
        session.flush()


def _to_params(model: Weights) -> WeightParams:
    """Convert a ``Weights`` ORM object to ``WeightParams`` dataclass."""
    return WeightParams(
        freshness=model.freshness,
        engagement=model.engagement,
        novelty=model.novelty,
        community_fit=model.community_fit,
        seasonality=model.seasonality,
    )


def get_weights() -> WeightParams:
    """Fetch weights from the database, creating defaults if necessary."""
    with session_scope() as session:
        weights = session.scalars(select(Weights)).first()
        if weights is None:
            weights = Weights(id=1)
            session.add(weights)
            session.flush()
        params = _to_params(weights)
    return params


def update_weights(*, smoothing: float = 1.0, **kwargs: float) -> WeightParams:
    """Update weight values using optional smoothing and return new model."""
    with session_scope() as session:
        weights = session.get(Weights, 1)
        if weights is None:
            weights = Weights(id=1)
            session.add(weights)
        for key, value in kwargs.items():
            if hasattr(weights, key):
                current = float(getattr(weights, key))
                target = float(value)
                setattr(weights, key, current * (1 - smoothing) + target * smoothing)
        session.flush()
        params = _to_params(weights)

    # Persist updated weights to a JSON file for durability
    try:
        WEIGHTS_FILE.write_text(json.dumps(asdict(params)))
    except Exception:  # pragma: no cover - persistence failures should not crash
        pass
    return params
