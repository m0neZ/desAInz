"""Tracing utilities using OpenTelemetry."""

from __future__ import annotations

from fastapi import FastAPI
from flask import Flask
from typing import Any, cast
from opentelemetry import trace

# The exporter classes are imported lazily within ``configure_tracing`` to avoid
# heavy dependencies and noisy warnings during package import.
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
import os
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_tracing(app: FastAPI | Flask, service_name: str) -> None:
    """Configure basic tracing for ``app``."""
    if os.getenv("OTEL_SDK_DISABLED", "false").lower() in {"true", "1"}:
        return
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter as OTLPGrpcSpanExporter,
    )
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter as OTLPHTTPSpanExporter,
    )

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")
    if protocol == "grpc":
        exporter: OTLPGrpcSpanExporter | OTLPHTTPSpanExporter = OTLPGrpcSpanExporter(
            endpoint=endpoint
        )
    else:
        exporter = OTLPHTTPSpanExporter(endpoint=endpoint)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    if isinstance(app, FastAPI):
        FastAPIInstrumentor.instrument_app(app)
    else:
        cast(Any, FlaskInstrumentor()).instrument_app(app)
