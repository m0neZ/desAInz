"""Locust scenarios for the API gateway service."""

from __future__ import annotations

import os

from locust import HttpUser, between, task


class ApiGatewayUser(HttpUser):
    """Exercise common API gateway endpoints."""

    host = os.getenv("GATEWAY_HOST", "http://localhost:8080")
    wait_time = between(1, 3)

    @task
    def status(self) -> None:
        """Fetch service status."""
        self.client.get("/status")

    @task
    def optimizations(self) -> None:
        """Request optimization suggestions."""
        self.client.get("/optimizations")
