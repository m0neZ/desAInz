"""Tracing utilities using OpenTelemetry."""

from __future__ import annotations

from fastapi import FastAPI
from flask import Flask
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
import os
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter


def configure_tracing(app: FastAPI | Flask, service_name: str) -> None:
    """Configure basic tracing for ``app``."""
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = JaegerExporter(
        agent_host_name=os.getenv("JAEGER_AGENT_HOST", "localhost"),
        agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
    )
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    if isinstance(app, FastAPI):
        FastAPIInstrumentor.instrument_app(app)
    else:
        FlaskInstrumentor().instrument_app(app)
