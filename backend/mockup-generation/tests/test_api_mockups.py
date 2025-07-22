"""Tests for listing generated mockups via the API."""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
import types
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import pytest
from fastapi.testclient import TestClient

root = Path(__file__).resolve().parents[3]
sys.path.append(str(root))
sys.path.append(str(root / "backend" / "mockup-generation"))

# Minimal stubs for optional dependencies
fastapi_mod = types.ModuleType("fastapi")
fastapi_mod.FastAPI = object
fastapi_mod.Request = object
fastapi_mod.Response = object
fastapi_mod.HTTPException = Exception
responses_mod = types.ModuleType("fastapi.responses")
responses_mod.JSONResponse = object
sys.modules.setdefault("fastapi.responses", responses_mod)
fastapi_mod.responses = responses_mod
sys.modules.setdefault("fastapi", fastapi_mod)

trace_root = types.ModuleType("opentelemetry.trace")
trace_root.set_tracer_provider = lambda *a, **k: None


class _DummySpan:
    def get_span_context(self) -> types.SimpleNamespace:
        return types.SimpleNamespace(trace_id=0)


trace_root.get_current_span = lambda: _DummySpan()
sys.modules.setdefault("opentelemetry.trace", trace_root)
fastapi_instr = types.ModuleType("opentelemetry.instrumentation.fastapi")
fastapi_instr.FastAPIInstrumentor = type(
    "FastAPIInstrumentor",
    (),
    {"instrument_app": lambda *a, **k: None},
)
sys.modules.setdefault("opentelemetry.instrumentation.fastapi", fastapi_instr)
flask_instr = types.ModuleType("opentelemetry.instrumentation.flask")
flask_instr.FlaskInstrumentor = object
sys.modules.setdefault("opentelemetry.instrumentation.flask", flask_instr)
res_mod = types.ModuleType("opentelemetry.sdk.resources")
res_mod.Resource = type(
    "Resource",
    (),
    {"create": staticmethod(lambda *a, **k: object())},
)
sys.modules.setdefault("opentelemetry.sdk.resources", res_mod)
trace_mod = types.ModuleType("opentelemetry.sdk.trace")
trace_mod.TracerProvider = type(
    "TracerProvider",
    (),
    {
        "__init__": lambda self, *a, **k: None,
        "add_span_processor": lambda *a, **k: None,
    },
)
sys.modules.setdefault("opentelemetry.sdk.trace", trace_mod)
export_mod = types.ModuleType("opentelemetry.sdk.trace.export")
export_mod.BatchSpanProcessor = type(
    "BatchSpanProcessor",
    (),
    {"__init__": lambda self, *a, **k: None},
)
sys.modules.setdefault("opentelemetry.sdk.trace.export", export_mod)
exp_http_mod = types.ModuleType("opentelemetry.exporter.otlp.proto.http.trace_exporter")
exp_http_mod.OTLPSpanExporter = type(
    "OTLPSpanExporter",
    (),
    {"__init__": lambda self, *a, **k: None},
)
sys.modules.setdefault(
    "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    exp_http_mod,
)

for name in [
    "opentelemetry",
    "opentelemetry.trace",
    "opentelemetry.instrumentation.fastapi",
    "opentelemetry.instrumentation.flask",
    "opentelemetry.sdk.resources",
    "opentelemetry.sdk.trace",
    "opentelemetry.sdk.trace.export",
    "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    "sentry_sdk",
    "sentry_sdk.integrations.asgi",
    "sentry_sdk.integrations.logging",
]:
    sys.modules.setdefault(name, types.ModuleType(name))

sentry_mod = sys.modules.setdefault("sentry_sdk", types.ModuleType("sentry_sdk"))
sentry_mod.init = lambda *args, **kwargs: None
sentry_mod.Hub = types.SimpleNamespace(current=types.SimpleNamespace(client=None))
sentry_asgi = sys.modules.setdefault(
    "sentry_sdk.integrations.asgi", types.ModuleType("sentry_sdk.integrations.asgi")
)
sentry_asgi.SentryAsgiMiddleware = object
logging_mod = sys.modules.setdefault(
    "sentry_sdk.integrations.logging",
    types.ModuleType("sentry_sdk.integrations.logging"),
)
logging_mod.LoggingIntegration = object

uc_mod = sys.modules.setdefault("UnleashClient", types.ModuleType("UnleashClient"))
uc_mod.UnleashClient = object
ld_mod = sys.modules.setdefault("ldclient", types.ModuleType("ldclient"))
ld_mod.LDClient = object
prom_mod = types.ModuleType("prometheus_client")
sys.modules["prometheus_client"] = prom_mod
prom_mod.CONTENT_TYPE_LATEST = ""
prom_mod.Counter = lambda *a, **k: types.SimpleNamespace(
    labels=lambda *_, **__: types.SimpleNamespace(inc=lambda *_, **__: None)
)
prom_mod.Gauge = lambda *a, **k: types.SimpleNamespace(
    inc=lambda *_, **__: None,
    dec=lambda *_, **__: None,
)
prom_mod.Histogram = lambda *a, **k: types.SimpleNamespace(
    labels=lambda *_, **__: types.SimpleNamespace(observe=lambda *_, **__: None)
)
prom_mod.REGISTRY = types.SimpleNamespace(register=lambda *a, **k: None)
prom_mod.generate_latest = lambda *a, **k: b""
sys.modules.setdefault("pgvector.sqlalchemy", types.ModuleType("pgvector.sqlalchemy"))
sys.modules["pgvector.sqlalchemy"].Vector = object


class DummyClient:
    """Collect uploaded objects."""

    async def put_object(self, Bucket: str, Key: str, Body: bytes | str) -> None:
        """Pretend to upload ``Body`` to ``Bucket/Key``."""
        return None


class DummyGenerator:
    """Generate a dummy file and keep track of cleanup."""

    def __init__(self) -> None:
        self.cleaned = False

    def generate(
        self,
        prompt: str,
        output: str,
        *,
        num_inference_steps: int = 30,
        model_identifier: str | None = None,
    ) -> types.SimpleNamespace:
        Path(output).write_text("x")
        return types.SimpleNamespace(image_path=output)

    def cleanup(self) -> None:
        self.cleaned = True


class DummyListing:
    """Simple listing container."""

    title = "t"
    description = "d"
    tags = ["a"]


class DummyListingGen:
    """Return :class:`DummyListing` instances."""

    def generate(self, keywords: list[str]) -> DummyListing:
        """Return listing regardless of ``keywords``."""
        return DummyListing()


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_metadata_recorded_and_listed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Generated mockups are saved and listed via the API."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    for mod in [
        "backend.shared.config",
        "backend.shared.db",
        "mockup_generation.model_repository",
        "mockup_generation.tasks",
        "mockup_generation.api",
    ]:
        sys.modules.pop(mod, None)
    tasks = importlib.import_module("mockup_generation.tasks")
    api = importlib.import_module("mockup_generation.api")
    monkeypatch.setattr(tasks, "generator", DummyGenerator())
    monkeypatch.setattr(tasks, "ListingGenerator", lambda: DummyListingGen())

    @asynccontextmanager
    async def _client() -> AsyncIterator[DummyClient]:
        yield DummyClient()

    monkeypatch.setattr(tasks, "_get_storage_client", _client)
    monkeypatch.setattr(
        tasks,
        "redis_client",
        types.SimpleNamespace(
            lock=lambda *a, **k: types.SimpleNamespace(
                acquire=lambda *a, **k: True,
                locked=lambda: False,
                release=lambda: None,
            )
        ),
    )

    class _Lock:
        async def acquire(self, *args: object, **kwargs: object) -> bool:
            return True

        def locked(self) -> bool:
            return False

        async def release(self) -> None:
            return None

    monkeypatch.setattr(
        tasks,
        "async_redis_client",
        types.SimpleNamespace(lock=lambda *a, **k: _Lock()),
    )
    monkeypatch.setattr(tasks, "remove_background", lambda img: img)
    monkeypatch.setattr(tasks, "convert_to_cmyk", lambda img: img)
    monkeypatch.setattr(tasks, "ensure_not_nsfw", lambda img: None)
    monkeypatch.setattr(tasks, "validate_dpi_image", lambda img: True)
    monkeypatch.setattr(tasks, "validate_color_space", lambda img: True)
    monkeypatch.setattr(tasks, "validate_dimensions", lambda img: True)
    monkeypatch.setattr(tasks, "validate_file_size", lambda p: True)
    tasks.settings.s3_bucket = "b"
    tasks.settings.s3_endpoint = "http://test"
    tasks.settings.s3_base_url = "http://cdn.test"

    tasks.generate_mockup.run([["kw"]], str(tmp_path), model="m", gpu_index=0)

    client = TestClient(api.app)
    resp = client.get("/mockups?limit=50&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "t"
