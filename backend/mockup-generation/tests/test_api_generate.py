"""Tests for /generate endpoint in mockup generation service."""

from __future__ import annotations

import sys
from pathlib import Path
import types
import warnings
from fastapi.testclient import TestClient
import pytest

root = Path(__file__).resolve().parents[3]
sys.path.append(str(root))
sys.path.append(str(root / "backend" / "mockup-generation"))

# Minimal stubs to satisfy imports performed in api.py
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

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
from mockup_generation import api  # noqa: E402

client = TestClient(api.app)

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


class DummyResult:
    """Return object from DummyCelery."""

    def __init__(self, id_: str) -> None:
        self.id = id_


class DummyCelery:
    """Collect Celery ``send_task`` calls."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, list[object], str | None]] = []

    def send_task(
        self, name: str, args: list[list[str]] | None = None, queue: str | None = None
    ) -> DummyResult:
        idx = len(self.sent)
        self.sent.append((name, args or [], queue))
        return DummyResult(f"task-{idx}")


def test_generate_success(monkeypatch: "pytest.MonkeyPatch") -> None:
    """Return task identifiers when payload is valid."""

    dummy = DummyCelery()
    monkeypatch.setattr(api, "celery_app", dummy)
    resp = client.post(
        "/generate",
        json={"batches": [["foo", "bar"], ["baz"]], "output_dir": "/tmp"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"tasks": ["task-0", "task-1"]}
    assert dummy.sent == [
        (
            "mockup_generation.tasks.generate_mockup",
            [["foo", "bar"], "/tmp"],
            None,
        ),
        (
            "mockup_generation.tasks.generate_mockup",
            [["baz"], "/tmp"],
            None,
        ),
    ]


def test_generate_bad_request() -> None:
    """Return 422 response for invalid payload."""

    resp = client.post("/generate", json={"batches": "foo", "output_dir": "/tmp"})
    assert resp.status_code == 422
