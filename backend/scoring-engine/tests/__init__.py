"""Test package configuration."""

import os
import sys

os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["SENTRY_DSN"] = ""
import backend.shared.errors as errors

errors.sentry_sdk = None


class DummyRedis:
    def __init__(self) -> None:
        import fakeredis

        self._client = fakeredis.FakeRedis()

    async def get(self, key: str) -> bytes | None:
        return self._client.get(key)

    async def setex(self, key: str, ttl: int, value: float) -> None:
        self._client.setex(key, ttl, value)

    async def incr(self, key: str) -> None:
        self._client.incr(key)

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)
