"""Tracing utilities using OpenTelemetry."""

from __future__ import annotations

from fastapi import FastAPI
from flask import Flask
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def configure_tracing(app: FastAPI | Flask, service_name: str) -> None:
    """Configure basic tracing for ``app``."""
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    if isinstance(app, FastAPI):
        FastAPIInstrumentor.instrument_app(app)
    else:
        FlaskInstrumentor().instrument_app(app)  # type: ignore
