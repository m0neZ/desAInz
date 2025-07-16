"""Flask application exposing scoring API."""

from __future__ import annotations

import json
import os

import logging
import uuid

from flask import Flask, Response, jsonify, request
import redis
from pydantic import BaseModel
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling
from backend.shared.logging import configure_logging
from backend.shared import configure_sentry

from backend.shared import add_flask_error_handlers

from datetime import datetime


class WeightsUpdate(BaseModel):
    """Request payload for updating weight parameters."""

    freshness: float
    engagement: float
    novelty: float
    community_fit: float
    seasonality: float


class ScoreRequest(BaseModel):
    """Request payload for scoring a signal."""

    timestamp: datetime
    engagement_rate: float
    embedding: list[float]
    metadata: dict[str, float] | None = None
    centroid: list[float] | None = None
    median_engagement: float | None = None
    topics: list[str] | None = None


from .scoring import Signal, calculate_score
from .weight_repository import get_weights, update_weights


configure_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)
configure_tracing(app, "scoring-engine")
configure_sentry(app, "scoring-engine")
add_profiling(app)
add_flask_error_handlers(app)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)


@app.before_request
def _before_request() -> None:
    """Attach a correlation ID before each request."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.correlation_id = correlation_id
    try:
        import sentry_sdk

        sentry_sdk.set_tag("correlation_id", correlation_id)
    except Exception:  # pragma: no cover - sentry optional
        pass
    logger.info("request received", extra={"correlation_id": correlation_id})


@app.after_request
def _after_request(response: Response) -> Response:
    """Propagate the correlation ID in responses."""
    correlation_id = getattr(request, "correlation_id", "-")
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.get("/weights")
def read_weights() -> Response:
    """Return current weighting parameters."""
    weights = get_weights()
    return jsonify(
        {
            "freshness": weights.freshness,
            "engagement": weights.engagement,
            "novelty": weights.novelty,
            "community_fit": weights.community_fit,
            "seasonality": weights.seasonality,
        }
    )


@app.put("/weights")
def update_weights_endpoint() -> Response:
    """Update weighting parameters via JSON payload."""
    body = WeightsUpdate(**request.get_json(force=True))
    weights = update_weights(**body.model_dump())
    return jsonify(
        {
            "freshness": weights.freshness,
            "engagement": weights.engagement,
            "novelty": weights.novelty,
            "community_fit": weights.community_fit,
            "seasonality": weights.seasonality,
        }
    )


@app.post("/score")
def score_signal() -> Response:
    """Score a signal and cache hot results."""
    payload = ScoreRequest(**request.get_json(force=True))
    key = json.dumps(payload.model_dump(), sort_keys=True)
    cached = redis_client.get(key)
    if cached is not None:
        return jsonify({"score": float(cached), "cached": True})
    signal = Signal(
        timestamp=payload.timestamp,
        engagement_rate=payload.engagement_rate,
        embedding=payload.embedding,
        metadata=payload.metadata or {},
    )
    centroid = payload.centroid or [0.0 for _ in payload.embedding]
    median_engagement = float(payload.median_engagement or 0)
    topics = payload.topics or []
    score = calculate_score(signal, centroid, median_engagement, topics)
    redis_client.setex(key, 3600, score)
    return jsonify({"score": score, "cached": False})


@app.get("/health")
def health() -> Response:
    """Return service liveness."""
    return jsonify(status="ok")


@app.get("/ready")
def ready() -> Response:
    """Return service readiness."""
    return jsonify(status="ready")


if __name__ == "__main__":
    app.run(debug=True, port=5002)
