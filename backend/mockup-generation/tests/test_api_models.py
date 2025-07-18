"""Tests for model management API in the mockup generation service."""

from __future__ import annotations

import sys
from pathlib import Path

import types
from fastapi.testclient import TestClient

root = Path(__file__).resolve().parents[3]
sys.path.append(str(root))  # noqa: E402
sys.path.append(str(root / "backend" / "mockup-generation"))  # noqa: E402

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
    "Resource", (), {"create": staticmethod(lambda *a, **k: object())}
)
sys.modules.setdefault("opentelemetry.sdk.resources", res_mod)
trace_mod = types.ModuleType("opentelemetry.sdk.trace")
trace_mod.TracerProvider = type(
    "TracerProvider",
    (),
    {
        "__init__": lambda self, *a, **k: None,
        "add_span_processor": lambda self, *a, **k: None,
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
sentry_asgi = sys.modules.setdefault(
    "sentry_sdk.integrations.asgi", types.ModuleType("sentry_sdk.integrations.asgi")
)
sentry_asgi.SentryAsgiMiddleware = object
logging_mod = sys.modules.setdefault(
    "sentry_sdk.integrations.logging",
    types.ModuleType("sentry_sdk.integrations.logging"),
)
logging_mod.LoggingIntegration = object

from mockup_generation.api import app  # noqa: E402
from mockup_generation.model_repository import list_models

client = TestClient(app)


def test_register_and_list_models() -> None:
    """Register a model and verify it appears in listings."""

    resp = client.post(
        "/models",
        json={
            "name": "base",
            "version": "1",
            "model_id": "model/a",
            "details": {},
            "is_default": True,
        },
    )
    assert resp.status_code == 200
    model_id = resp.json()["id"]
    models = [m for m in list_models() if m.id == model_id]
    assert models


def test_switch_default_model() -> None:
    """Switch model via the service API."""

    resp = client.post(
        "/models",
        json={
            "name": "alt",
            "version": "2",
            "model_id": "model/b",
        },
    )
    model_id = resp.json()["id"]
    resp = client.post(f"/models/{model_id}/default")
    assert resp.status_code == 200
    models = list_models()
    assert any(m.id == model_id and m.is_default for m in models)
