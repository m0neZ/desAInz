"""Integration tests for tracing configuration."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest
from fastapi import FastAPI
from opentelemetry import trace

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))


def test_configure_tracing_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exporter endpoint and protocol should be read from env vars."""
    called = {}

    class DummyExporter:
        def __init__(self, endpoint: str | None = None) -> None:
            called["endpoint"] = endpoint

    grpc_mod = types.ModuleType("opentelemetry.exporter.otlp.proto.grpc.trace_exporter")
    setattr(grpc_mod, "OTLPSpanExporter", DummyExporter)
    http_mod = types.ModuleType("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    setattr(http_mod, "OTLPSpanExporter", DummyExporter)
    monkeypatch.setitem(sys.modules, grpc_mod.__name__, grpc_mod)
    monkeypatch.setitem(sys.modules, http_mod.__name__, http_mod)

    class DummyTracerProvider:
        def __init__(self, resource: object) -> None:  # noqa: D401
            self.resource = resource

        def add_span_processor(self, processor: object) -> None:
            self.processor = processor

    monkeypatch.setitem(
        sys.modules,
        "opentelemetry.sdk.trace",
        types.ModuleType("opentelemetry.sdk.trace"),
    )
    sys.modules["opentelemetry.sdk.trace"].TracerProvider = DummyTracerProvider  # type: ignore[attr-defined]

    monkeypatch.setitem(
        sys.modules,
        "opentelemetry.sdk.trace.export",
        types.ModuleType("opentelemetry.sdk.trace.export"),
    )
    sys.modules["opentelemetry.sdk.trace.export"].BatchSpanProcessor = (  # type: ignore[attr-defined]
        lambda exporter: None
    )

    provider_holder: dict[str, object] = {}
    monkeypatch.setitem(
        sys.modules,
        "opentelemetry.trace",
        types.SimpleNamespace(
            set_tracer_provider=lambda p: provider_holder.setdefault("provider", p)
        ),
    )

    app = FastAPI()
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4317")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    monkeypatch.setenv("OTEL_SDK_DISABLED", "false")

    tracing = importlib.import_module("backend.shared.tracing")
    importlib.reload(tracing)
    tracing.configure_tracing(app, "test-service")

    assert called["endpoint"] == "http://collector:4317"
    provider = provider_holder["provider"]
    assert isinstance(provider, DummyTracerProvider)
