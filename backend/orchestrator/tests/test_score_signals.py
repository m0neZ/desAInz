"""Tests for score_signals op concurrency."""

from __future__ import annotations

import asyncio
from time import perf_counter
from pathlib import Path
import sys

import httpx
import pytest
from dagster import build_op_context

ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT / "backend" / "orchestrator"))  # noqa: E402
MONITORING_SRC = ROOT / "backend" / "monitoring" / "src"
sys.path.append(str(MONITORING_SRC))  # noqa: E402

from orchestrator.ops import score_signals  # noqa: E402


@pytest.mark.asyncio()
async def test_score_signals_concurrent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure scoring requests are executed concurrently."""

    async def fake_post(
        self: object, url: str, *args: object, **kwargs: object
    ) -> object:
        await asyncio.sleep(0.1)

        class Resp:
            def raise_for_status(self) -> None:  # noqa: D401 - test helper
                return None

            def json(self) -> dict[str, float]:  # noqa: D401 - test helper
                return {"score": 1.0}

        return Resp()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    monkeypatch.setenv("SCORE_CONCURRENCY", "3")

    ctx = build_op_context()
    signals = ["s1", "s2", "s3"]
    start = perf_counter()
    scores = await score_signals.compute_fn.decorated_fn(ctx, signals)
    duration = perf_counter() - start

    assert scores == [1.0, 1.0, 1.0]
    assert duration < 0.3


@pytest.mark.asyncio()
async def test_score_signals_respects_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure the semaphore prevents too many concurrent requests."""

    async def fake_post(
        self: object, url: str, *args: object, **kwargs: object
    ) -> object:
        await asyncio.sleep(0.1)

        class Resp:
            def raise_for_status(self) -> None:  # noqa: D401 - test helper
                return None

            def json(self) -> dict[str, float]:  # noqa: D401 - test helper
                return {"score": 1.0}

        return Resp()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setenv("SCORE_CONCURRENCY", "1")

    ctx = build_op_context()
    signals = ["s1", "s2", "s3"]
    start = perf_counter()
    scores = await score_signals.compute_fn.decorated_fn(ctx, signals)
    duration = perf_counter() - start

    assert scores == [1.0, 1.0, 1.0]
    assert duration >= 0.3
