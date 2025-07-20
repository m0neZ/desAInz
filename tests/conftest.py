"""Global pytest fixtures for the test suite."""

from __future__ import annotations

import os
import sys
from types import ModuleType, SimpleNamespace
import warnings

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
import fakeredis.aioredis

os.environ.setdefault("OTEL_SDK_DISABLED", "true")
warnings.filterwarnings(
    "ignore", category=UserWarning, message='directory "/run/secrets" does not exist'
)

# Stub OpenTelemetry exporter to avoid heavy dependencies during tests.
_trace_exporter = ModuleType("opentelemetry.exporter.otlp.proto.http.trace_exporter")
_trace_exporter.OTLPSpanExporter = object
sys.modules.setdefault(
    "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    _trace_exporter,
)


class _DummyProducer:
    def __init__(self, *args, **kwargs):
        pass

    def send(self, *args, **kwargs):
        pass

    def flush(self) -> None:  # pragma: no cover
        pass


class _DummyConsumer:
    def __init__(self, *args, **kwargs):
        pass

    def __iter__(self):
        return iter([])


@pytest.fixture(autouse=True)
def _stub_services(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub external dependencies like Kafka and Selenium."""
    os.environ.setdefault("KAFKA_SKIP", "1")
    os.environ.setdefault("SELENIUM_SKIP", "1")

    monkeypatch.setattr("kafka.KafkaProducer", _DummyProducer, raising=False)
    monkeypatch.setattr("kafka.KafkaConsumer", _DummyConsumer, raising=False)
    monkeypatch.setattr(
        "selenium.webdriver.Firefox",
        lambda *a, **k: SimpleNamespace(get=lambda *a, **k: None),
        raising=False,
    )


@pytest.fixture()
async def sqlite_engine() -> AsyncEngine:
    """Return an in-memory SQLite engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture()
def session_factory(sqlite_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Return a session factory bound to ``sqlite_engine``."""
    return async_sessionmaker(sqlite_engine, expire_on_commit=False)


@pytest.fixture()
def fake_redis() -> fakeredis.aioredis.FakeRedis:
    """Return a fakeredis instance."""
    return fakeredis.aioredis.FakeRedis()
