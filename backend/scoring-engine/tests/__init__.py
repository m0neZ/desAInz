"""Test package configuration."""

import os
import sys
import warnings

os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["SENTRY_DSN"] = ""
warnings.filterwarnings(
    "ignore",
    message='directory "/run/secrets" does not exist',
)
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")),
)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:  # pragma: no cover - optional dependency
    import backend.shared.errors as errors  # noqa: E402

    errors.sentry_sdk = None
except Exception:  # pragma: no cover - ignore if import fails
    pass


class DummyRedis:
    """Simple asynchronous wrapper around :class:`fakeredis.FakeRedis`."""

    def __init__(self) -> None:
        """Initialize fake Redis client."""
        import fakeredis

        self._client = fakeredis.FakeRedis()

    async def get(self, key: str) -> bytes | None:
        """Return value for ``key`` if present."""
        return self._client.get(key)

    async def setex(self, key: str, ttl: int, value: float) -> None:
        """Set ``key`` with ``ttl`` and ``value``."""
        self._client.setex(key, ttl, value)

    async def incr(self, key: str) -> None:
        """Increment ``key`` counter."""
        self._client.incr(key)


sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")),
)
