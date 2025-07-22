"""Baseline Locust scenarios for desAInz APIs."""

# mypy: ignore-errors

from __future__ import annotations

import os

from locust import HttpUser, between, task


class IngestionApiUser(HttpUser):
    """Exercise the ingestion API."""

    host = os.getenv("INGESTION_HOST", "http://localhost:8004")
    wait_time = between(1, 3)

    @task
    def ingest(self) -> None:
        self.client.post("/ingest")


class ScoringApiUser(HttpUser):
    """Exercise the scoring API."""

    host = os.getenv("SCORING_HOST", "http://localhost:5002")
    wait_time = between(1, 3)

    @task
    def score(self) -> None:
        payload = {
            "timestamp": "2024-01-01T00:00:00Z",
            "engagement_rate": 1.0,
            "embedding": [0.1, 0.2],
            "metadata": {},
        }
        self.client.post("/score", json=payload)


class PublishingApiUser(HttpUser):
    """Exercise the publishing API."""

    host = os.getenv("PUBLISHING_HOST", "http://localhost:8001")
    wait_time = between(1, 3)

    @task
    def publish(self) -> None:
        payload = {
            "marketplace": "AMAZON",
            "design_path": "example",
            "metadata": {},
        }
        self.client.post("/publish", json=payload)
