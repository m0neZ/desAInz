"""Enumerate backend service names."""

from __future__ import annotations

from enum import Enum


class ServiceName(str, Enum):
    """Names of backend services."""

    API_GATEWAY = "api-gateway"
    ANALYTICS = "analytics"
    FEEDBACK_LOOP = "feedback-loop"
    MARKETPLACE_PUBLISHER = "marketplace-publisher"
    MOCKUP_GENERATION = "mockup-generation"
    MONITORING = "monitoring"
    OPTIMIZATION = "optimization"
    ORCHESTRATOR = "orchestrator"
    SCORING_ENGINE = "scoring-engine"
    SIGNAL_INGESTION = "signal-ingestion"
