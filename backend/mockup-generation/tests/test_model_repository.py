"""Tests for generated mockup repository functions."""

from __future__ import annotations

import sys
from pathlib import Path
import types
import warnings

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

flask_mod = types.ModuleType("flask")
flask_mod.Flask = object
flask_mod.request = object()
flask_mod.jsonify = lambda *args, **kwargs: ""
flask_mod.Response = object
sys.modules.setdefault("flask", flask_mod)

otel_mod = types.ModuleType("opentelemetry")
otel_mod.trace = object()
sys.modules.setdefault("opentelemetry", otel_mod)

fastapi_instr = types.ModuleType("opentelemetry.instrumentation.fastapi")
fastapi_instr.FastAPIInstrumentor = object
sys.modules.setdefault("opentelemetry.instrumentation.fastapi", fastapi_instr)

flask_instr = types.ModuleType("opentelemetry.instrumentation.flask")
flask_instr.FlaskInstrumentor = object
sys.modules.setdefault("opentelemetry.instrumentation.flask", flask_instr)

res_mod = types.ModuleType("opentelemetry.sdk.resources")
res_mod.Resource = object
sys.modules.setdefault("opentelemetry.sdk.resources", res_mod)

trace_mod = types.ModuleType("opentelemetry.sdk.trace")
trace_mod.TracerProvider = object
sys.modules.setdefault("opentelemetry.sdk.trace", trace_mod)

export_mod = types.ModuleType("opentelemetry.sdk.trace.export")
export_mod.BatchSpanProcessor = object
sys.modules.setdefault("opentelemetry.sdk.trace.export", export_mod)

exp_http_mod = types.ModuleType("opentelemetry.exporter.otlp.proto.http.trace_exporter")
exp_http_mod.OTLPSpanExporter = object
sys.modules.setdefault(
    "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    exp_http_mod,
)

for name in [
    "flask",
    "opentelemetry",
    "opentelemetry.sdk.resources",
    "opentelemetry.sdk.trace",
    "opentelemetry.sdk.trace.export",
    "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    "sentry_sdk",
    "sentry_sdk.integrations.asgi",
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
uc_mod = sys.modules.setdefault("UnleashClient", types.ModuleType("UnleashClient"))
uc_mod.UnleashClient = object
ld_mod = sys.modules.setdefault("ldclient", types.ModuleType("ldclient"))
ld_mod.LDClient = object
prom_mod = sys.modules.setdefault(
    "prometheus_client", types.ModuleType("prometheus_client")
)
prom_mod.CONTENT_TYPE_LATEST = ""
prom_mod.Counter = lambda *a, **k: types.SimpleNamespace(
    labels=lambda *_, **__: types.SimpleNamespace(inc=lambda *_, **__: None)
)
prom_mod.Histogram = lambda *a, **k: types.SimpleNamespace(
    labels=lambda *_, **__: types.SimpleNamespace(observe=lambda *_, **__: None)
)
prom_mod.generate_latest = lambda *a, **k: b""
sys.modules.setdefault("pgvector.sqlalchemy", types.ModuleType("pgvector.sqlalchemy"))
sys.modules["pgvector.sqlalchemy"].Vector = object
warnings.filterwarnings("ignore", category=UserWarning)

from mockup_generation.model_repository import (  # noqa: E402
    list_generated_mockups,
    save_generated_mockup,
)


def test_save_and_list_generated_mockups() -> None:
    """Insert a record and retrieve it."""
    save_generated_mockup(
        "a prompt",
        10,
        123,
        "uri",
        "title",
        "desc",
        ["t"],
    )
    items = list_generated_mockups()
    assert any(
        i.prompt == "a prompt"
        and i.num_inference_steps == 10
        and i.seed == 123
        and i.image_uri == "uri"
        for i in items
    )
