"""OpenTelemetry tracing configuration utilities."""

from __future__ import annotations

from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


def _configure_tracer(service_name: str) -> None:
    """Configure the tracer provider for ``service_name``."""
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    processor = SimpleSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


def init_fastapi_tracing(app: Any, service_name: str) -> None:
    """Instrument a FastAPI ``app`` for tracing."""
    _configure_tracer(service_name)
    FastAPIInstrumentor().instrument_app(app)


def init_flask_tracing(app: Any, service_name: str) -> None:
    """Instrument a Flask ``app`` for tracing."""
    _configure_tracer(service_name)
    try:
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
    except Exception:  # pragma: no cover - Flask not installed
        return
    FlaskInstrumentor().instrument_app(app)  # type: ignore[no-untyped-call]


def init_celery_tracing(app: Any, service_name: str) -> None:
    """Instrument a Celery ``app`` for tracing."""
    _configure_tracer(service_name)
    try:
        from opentelemetry.instrumentation.celery import CeleryInstrumentor
    except Exception:  # pragma: no cover - Celery not installed
        return
    CeleryInstrumentor().instrument()
