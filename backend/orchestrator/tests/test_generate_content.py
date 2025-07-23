"""Tests for generate_content op concurrency."""

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

from orchestrator.ops import generate_content  # noqa: E402


@pytest.mark.asyncio()
async def test_generate_content_respects_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure generation requests adhere to ``GEN_CONCURRENCY``."""

    async def fake_post(
        self: object, url: str, *args: object, **kwargs: object
    ) -> object:
        await asyncio.sleep(0.1)

        class Resp:
            def raise_for_status(self) -> None:  # noqa: D401 - test helper
                return None

            def json(self) -> dict[str, list[str]]:  # noqa: D401 - test helper
                return {"items": ["i1"]}

        return Resp()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setenv("GEN_CONCURRENCY", "1")

    ctx = build_op_context()
    scores = [0.1, 0.2, 0.3]
    start = perf_counter()
    items = await generate_content.compute_fn.decorated_fn(ctx, scores)
    duration = perf_counter() - start

    assert items == ["i1", "i1", "i1"]
    assert duration >= 0.3
