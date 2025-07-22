"""Tests for the unified CLI."""

from __future__ import annotations

from contextlib import AsyncExitStack
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scripts.cli import app

runner = CliRunner()


def test_ingest_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure ingest triggers ingestion logic."""

    called: dict[str, bool] = {"ingest": False}

    async def fake_ingest(session: object) -> None:
        called["ingest"] = True

    async def fake_init_db() -> None:  # pragma: no cover - patched
        called["init"] = True

    monkeypatch.setattr("signal_ingestion.ingestion.ingest", fake_ingest)
    monkeypatch.setattr("signal_ingestion.database.init_db", fake_init_db)
    monkeypatch.setattr(
        "signal_ingestion.database.async_session_scope",
        lambda: AsyncExitStack(),
    )
    result = runner.invoke(app, ["ingest"])
    assert result.exit_code == 0
    assert called["ingest"]


def test_score_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """Calculate score using patched function."""

    def fake_calculate(
        signal: object, median_engagement: float, topics: list[str]
    ) -> float:
        assert median_engagement == 0.0
        return 1.23

    monkeypatch.setattr("scoring_engine.scoring.calculate_score", fake_calculate)
    result = runner.invoke(app, ["score", "0.5", "0.1", "0.2"])
    assert result.exit_code == 0
    assert "1.23" in result.output


def test_generate_mockups_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Invoke generate mockups using a stubbed generator."""

    class Dummy:
        def generate(
            self, prompt: str, path: str, num_inference_steps: int = 30
        ) -> object:
            (tmp_path / "img.png").write_text("img")
            return type("R", (), {"image_path": tmp_path / "img.png"})()

    monkeypatch.setattr("mockup_generation.generator.MockupGenerator", lambda: Dummy())
    result = runner.invoke(
        app,
        ["generate-mockups", "p", "--output-dir", str(tmp_path), "--steps", "1"],
    )
    assert result.exit_code == 0
    assert (tmp_path / "img.png").exists()


def test_publish_command(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Publish task creation and retry are called."""

    called: dict[str, bool] = {"task": False, "publish": False, "init": False}

    async def fake_init_db() -> None:
        called["init"] = True

    async def fake_create_task(session: object, **kwargs: object) -> object:
        called["task"] = True
        return type("T", (), {"id": 1, "marketplace": "redbubble"})()

    async def fake_publish(
        session: object,
        task_id: int,
        marketplace: object,
        design_path: Path,
        metadata: dict[str, object],
        max_attempts: int = 1,
    ) -> None:
        called["publish"] = True

    monkeypatch.setattr("marketplace_publisher.db.init_db", fake_init_db)
    monkeypatch.setattr("marketplace_publisher.db.create_task", fake_create_task)
    monkeypatch.setattr(
        "marketplace_publisher.publisher.publish_with_retry", fake_publish
    )
    monkeypatch.setattr(
        "marketplace_publisher.db.SessionLocal", lambda: AsyncExitStack()
    )
    design = tmp_path / "d.png"
    design.write_text("img")
    result = runner.invoke(app, ["publish", str(design), "redbubble"])
    assert result.exit_code == 0
    assert called["publish"]
