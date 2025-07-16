"""Tests for the Dagster orchestrator."""

from orchestrator.jobs import idea_job


def test_job_structure() -> None:
    """Verify job includes all steps in order."""
    ops = [op.name for op in idea_job.graph.node_dict.values()]
    assert ops == [
        "ingest_signals",
        "score_signals",
        "generate_content",
        "await_approval",
        "publish_content",
    ]
