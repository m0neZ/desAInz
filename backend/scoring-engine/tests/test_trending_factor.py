import importlib
from typing import Any

import fakeredis.aioredis
import pytest

scoring_module = importlib.import_module("scoring_engine.app")


@pytest.mark.asyncio
async def test_trending_factor_pipeline(monkeypatch: Any) -> None:
    client = fakeredis.aioredis.FakeRedis()
    await client.zadd("trending:keywords", {"foo": 10.0, "bar": 20.0})
    monkeypatch.setattr(scoring_module, "redis_client", client)
    factor = await scoring_module.trending_factor(["foo", "bar", "baz"])
    assert factor == pytest.approx(1.2)
