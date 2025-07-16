"""Dagster job definitions for the orchestrator."""

from __future__ import annotations

import os
from dagster import Failure, RetryPolicy, job, op


@op(retry_policy=RetryPolicy(max_retries=3))
def ingestion() -> str:
    """Return raw data as the ingestion step."""
    return "raw data"


@op(retry_policy=RetryPolicy(max_retries=3))
def scoring(data: str) -> float:
    """Compute a score for the ingested data."""
    return float(len(data))


@op(retry_policy=RetryPolicy(max_retries=3))
def generation(score: float) -> str:
    """Generate content based on the score."""
    return f"content with score {score}"


@op(retry_policy=RetryPolicy(max_retries=3))
def approval_gate(content: str) -> str:
    """Require manual approval before publishing.

    Raises:
        Failure: If the ``APPROVE_PUBLISH`` environment variable is not set to
            ``"true"``.
    """
    if os.getenv("APPROVE_PUBLISH", "false").lower() != "true":
        raise Failure("Publishing not approved")
    return content


@op(retry_policy=RetryPolicy(max_retries=3))
def publishing(content: str) -> None:
    """Publish the generated content."""
    print(f"Published: {content}")


@job
def pipeline() -> None:
    """Full pipeline from ingestion to publishing."""
    data = ingestion()
    score = scoring(data)
    content = generation(score)
    approved = approval_gate(content)
    publishing(approved)
