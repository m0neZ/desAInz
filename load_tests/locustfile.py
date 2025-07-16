"""Load tests for desAInz API endpoints using Locust."""
# flake8: noqa: D102
# pydocstyle: ignore=D102

from __future__ import annotations

import os
from locust import HttpUser, task, between, events

THRESHOLD_FAILURE_RATIO = float(os.environ.get("THRESHOLD_FAILURE_RATIO", "0.01"))
THRESHOLD_AVG_RESPONSE_TIME = float(
    os.environ.get("THRESHOLD_AVG_RESPONSE_TIME", "1000")
)


@events.quitting.add_listener
def _(environment, **_kwargs) -> None:
    """Set exit code based on performance thresholds."""
    stats = environment.stats.total
    if stats.fail_ratio > THRESHOLD_FAILURE_RATIO:
        environment.process_exit_code = 1
    elif stats.avg_response_time > THRESHOLD_AVG_RESPONSE_TIME:
        environment.process_exit_code = 1
    else:
        environment.process_exit_code = 0


class ServiceTemplateUser(HttpUser):
    """Load profile for the service-template endpoints."""

    host = os.getenv("SERVICE_TEMPLATE_HOST", "http://localhost:8000")
    wait_time = between(1, 3)

    @task
    def health(self) -> None:
        self.client.get("/health")

    @task
    def ready(self) -> None:
        self.client.get("/ready")


class MarketplacePublisherUser(HttpUser):
    """Load profile for the marketplace-publisher service."""

    host = os.getenv("MARKETPLACE_PUBLISHER_HOST", "http://localhost:8001")
    wait_time = between(1, 3)

    @task
    def publish(self) -> None:
        payload = {"marketplace": "AMAZON", "design_path": "example", "metadata": {}}
        self.client.post("/publish", json=payload)

    @task
    def progress(self) -> None:
        self.client.get("/progress/1")

    @task
    def health(self) -> None:
        self.client.get("/health")

    @task
    def ready(self) -> None:
        self.client.get("/ready")


class MonitoringUser(HttpUser):
    """Load profile for the monitoring service."""

    host = os.getenv("MONITORING_HOST", "http://localhost:8002")
    wait_time = between(1, 3)

    @task
    def metrics(self) -> None:
        self.client.get("/metrics")

    @task
    def overview(self) -> None:
        self.client.get("/overview")

    @task
    def analytics(self) -> None:
        self.client.get("/analytics")

    @task
    def logs(self) -> None:
        self.client.get("/logs")


class OptimizationUser(HttpUser):
    """Load profile for the optimization service."""

    host = os.getenv("OPTIMIZATION_HOST", "http://localhost:8003")
    wait_time = between(1, 3)

    @task
    def add_metric(self) -> None:
        payload = {
            "timestamp": "2024-01-01T00:00:00Z",
            "cpu_percent": 50,
            "memory_mb": 512,
        }
        self.client.post("/metrics", json=payload)

    @task
    def optimizations(self) -> None:
        self.client.get("/optimizations")


class ScoringEngineUser(HttpUser):
    """Load profile for the scoring-engine service."""

    host = os.getenv("SCORING_ENGINE_HOST", "http://localhost:5002")
    wait_time = between(1, 3)

    @task
    def read_weights(self) -> None:
        self.client.get("/weights")

    @task
    def update_weights(self) -> None:
        data = {
            "freshness": 1.0,
            "engagement": 1.0,
            "novelty": 1.0,
            "community_fit": 1.0,
            "seasonality": 1.0,
        }
        self.client.put("/weights", json=data)

    @task
    def score(self) -> None:
        payload = {
            "timestamp": "2024-01-01T00:00:00Z",
            "engagement_rate": 1.0,
            "embedding": [0.1, 0.2],
            "metadata": {},
        }
        self.client.post("/score", json=payload)


class SignalIngestionUser(HttpUser):
    """Load profile for the signal-ingestion service."""

    host = os.getenv("SIGNAL_INGESTION_HOST", "http://localhost:8004")
    wait_time = between(1, 3)

    @task
    def ingest(self) -> None:
        self.client.post("/ingest")

    @task
    def health(self) -> None:
        self.client.get("/health")

    @task
    def ready(self) -> None:
        self.client.get("/ready")
