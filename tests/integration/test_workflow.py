"""Integration tests for the full workflow."""

from __future__ import annotations

from pathlib import Path

import vcr

from src.ingestion import fetch_signals
from src.mockup import generate_mockups
from src.publishing import publish
from src.scoring import score_signals

CASSETTE = Path(__file__).parent / "cassettes" / "ingestion.yaml"


@vcr.use_cassette(str(CASSETTE))
def test_workflow(tmp_path: Path) -> None:
    """Run ingestion, scoring, mockup generation and publishing."""
    signals = fetch_signals("https://jsonplaceholder.typicode.com/todos/1")
    scored = score_signals(signals)
    mockups = generate_mockups(scored)
    output_file = tmp_path / "result.txt"
    publish(mockups, str(output_file))
    assert output_file.exists()
    content = output_file.read_text()
    assert "mockup-for" in content
