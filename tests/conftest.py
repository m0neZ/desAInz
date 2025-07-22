"""Global pytest fixtures for the test suite."""

from __future__ import annotations

import os
import sys
from importlib import util as importlib_util
from pathlib import Path
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
import psycopg2
import time
import docker

os.environ.setdefault("OTEL_SDK_DISABLED", "true")
warnings.filterwarnings(
    "ignore", category=UserWarning, message='directory "/run/secrets" does not exist'
)

# Inject lightweight stubs for heavy optional dependencies.
if os.environ.get("SKIP_HEAVY_DEPS") == "1":
    stubs_dir = Path(__file__).parent / "stubs"
    for stub_path in stubs_dir.glob("*.py"):
        module_name = stub_path.stem
        if module_name in sys.modules:
            continue
        spec = importlib_util.spec_from_file_location(module_name, stub_path)
        module = importlib_util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        sys.modules[module_name] = module

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


class _PostgresConnectionWrapper:
    """Wrapper for a psycopg2 connection with ``info.dsn`` attribute."""

    def __init__(self, conn: psycopg2.extensions.connection, dsn: str) -> None:
        self._conn = conn
        self.info = SimpleNamespace(dsn=dsn)

    def __getattr__(self, name: str) -> object:
        return getattr(self._conn, name)


@pytest.fixture()
def postgresql() -> _PostgresConnectionWrapper:
    """Spin up a temporary PostgreSQL instance using Docker."""
    client = docker.from_env()
    container = client.containers.run(
        "postgres:15",
        environment={
            "POSTGRES_USER": "user",
            "POSTGRES_PASSWORD": "password",
            "POSTGRES_DB": "test",
        },
        ports={"5432/tcp": None},
        detach=True,
    )
    try:
        container.reload()
        port = container.attrs["NetworkSettings"]["Ports"]["5432/tcp"][0]["HostPort"]
        dsn = f"postgresql://user:password@localhost:{port}/test"
        for _ in range(30):
            try:
                conn = psycopg2.connect(dsn)
                break
            except psycopg2.OperationalError:
                time.sleep(1)
        else:
            raise RuntimeError("PostgreSQL container failed to start")
        wrapper = _PostgresConnectionWrapper(conn, dsn)
        try:
            yield wrapper
        finally:
            conn.close()
    finally:
        container.remove(force=True)
