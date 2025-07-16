"""Flask application exposing scoring API."""

from __future__ import annotations

import json
import os

from flask import Flask, Response, jsonify, request
import redis
from backend.shared.tracing import configure_tracing

from datetime import datetime

from .scoring import Signal, calculate_score
from .weight_repository import get_weights, update_weights

app = Flask(__name__)
configure_tracing(app, "scoring-engine")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)


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
    data = request.get_json(force=True)
    weights = update_weights(**data)
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
    payload = request.get_json(force=True)
    key = json.dumps(payload, sort_keys=True)
    cached = redis_client.get(key)
    if cached is not None:
        return jsonify({"score": float(cached), "cached": True})
    signal = Signal(
        timestamp=datetime.fromisoformat(payload["timestamp"]),
        engagement_rate=float(payload["engagement_rate"]),
        embedding=payload["embedding"],
        metadata=payload.get("metadata", {}),
    )
    centroid = payload.get("centroid", [0.0 for _ in payload["embedding"]])
    median_engagement = float(payload.get("median_engagement", 0))
    topics = payload.get("topics", [])
    score = calculate_score(signal, centroid, median_engagement, topics)
    redis_client.setex(key, 3600, score)
    return jsonify({"score": score, "cached": False})


if __name__ == "__main__":
    app.run(debug=True, port=5002)
