"""Utilities for configuring OpenTelemetry tracing."""

from __future__ import annotations

from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_tracing(service_name: str, app: Any | None = None) -> None:
    """Configure a basic OTLP exporter and instrument ``app`` if provided."""
    resource = Resource(attributes={SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    if app is not None:
        try:
            from fastapi import FastAPI
            from flask import Flask
        except Exception:  # pragma: no cover - defensive import
            FastAPI = None
            Flask = None

        if FastAPI is not None and isinstance(app, FastAPI):
            FastAPIInstrumentor.instrument_app(app)
        elif Flask is not None and isinstance(app, Flask):
            FlaskInstrumentor().instrument_app(app)
