"""Dagster jobs composing the orchestration pipeline."""

from __future__ import annotations

from dagster import job

from .ops import (
    await_approval,
    generate_content,
    ingest_signals,
    publish_content,
    score_signals,
)


@job
def idea_job() -> None:
    """Pipeline from ingestion to publishing."""
    payload = ingest_signals()
    payload = score_signals(payload)
    payload = generate_content(payload)
    await_approval()
    publish_content(payload)
