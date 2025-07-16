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
    signals = ingest_signals()
    scores = score_signals(signals)
    items = generate_content(scores)
    await_approval()
    publish_content(items)
