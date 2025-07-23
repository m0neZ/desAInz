"""Unified command line interface for desAInz operations."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import List

import typer


app = typer.Typer(add_completion=False, help="Operations helpers")


@app.command()
def ingest() -> None:
    """Run signal ingestion once."""

    async def _run() -> None:
        from signal_ingestion.database import async_session_scope, init_db
        from signal_ingestion.ingestion import ingest as ingest_signals

        await init_db()
        async with async_session_scope() as session:
            await ingest_signals(session)

    asyncio.run(_run())


@app.command()
def score(engagement_rate: float, embedding: List[float]) -> None:
    """Calculate a score for a single signal."""
    from scoring_engine.scoring import Signal, calculate_score

    signal = Signal(
        source="cli",
        timestamp=datetime.utcnow().replace(tzinfo=UTC),
        engagement_rate=engagement_rate,
        embedding=embedding,
        metadata={},
    )
    result = calculate_score(signal, median_engagement=0.0, topics=[])
    typer.echo(f"score: {result}")


@app.command("generate-mockups")
def generate_mockups(
    prompt: str,
    output_dir: Path = Path("mockups"),
    steps: int = 30,
) -> None:
    """Generate a mockup for ``prompt``."""
    from mockup_generation.generator import MockupGenerator

    output_dir.mkdir(parents=True, exist_ok=True)

    async def _run() -> None:
        generator = MockupGenerator()
        result = await generator.generate(
            prompt, str(output_dir / "mockup.png"), num_inference_steps=steps
        )
        typer.echo(str(result.image_path))

    asyncio.run(_run())


@app.command()
def publish(
    design_path: Path,
    marketplace: str,
    metadata: str = "{}",
) -> None:
    """Publish ``design_path`` to ``marketplace``."""

    async def _run() -> None:
        from marketplace_publisher import db, publisher

        await db.init_db()
        meta = json.loads(metadata)
        async with db.SessionLocal() as session:
            task = await db.create_task(
                session,
                marketplace=db.Marketplace(marketplace),
                design_path=str(design_path),
                metadata_json=metadata,
            )
            await publisher.publish_with_retry(
                session,
                task.id,
                db.Marketplace(marketplace),
                design_path,
                meta,
                max_attempts=1,
            )

    asyncio.run(_run())


if __name__ == "__main__":  # pragma: no cover
    app()
