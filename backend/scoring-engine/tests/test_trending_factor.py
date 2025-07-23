"""Test the trending factor pipeline for the scoring engine."""

from typing import Any

import fakeredis.aioredis
import pytest


async def trending_factor(topics: list[str], redis_client: Any) -> float:
    """Return multiplier based on cached trending topics."""

    if not topics:
        return 1.0
    pipe = redis_client.pipeline()
    for topic in topics:
        pipe.zscore("trending:keywords", topic)
    scores = await pipe.execute()
    max_score = max((score or 0.0) for score in scores)
    return 1.0 + max_score / 100.0


@pytest.mark.asyncio
async def test_trending_factor_pipeline() -> None:
    """Validate score scaling based on trending keywords."""

    client = fakeredis.aioredis.FakeRedis()
    await client.zadd("trending:keywords", {"foo": 10.0, "bar": 20.0})

    factor = await trending_factor(["foo", "bar", "baz"], client)
    assert factor == pytest.approx(1.2)
