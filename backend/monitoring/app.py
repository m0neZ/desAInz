"""Monitoring service exposing Prometheus metrics and basic endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, cast

from flask import Flask, Response, jsonify
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from prometheus_client import CollectorRegistry, Counter, generate_latest


app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)  # type: ignore[no-untyped-call]

trace.set_tracer_provider(
    TracerProvider(resource=Resource.create({SERVICE_NAME: "monitoring"}))
)
tracer = trace.get_tracer(__name__)
span_processor = SimpleSpanProcessor(ConsoleSpanExporter())
provider = cast(TracerProvider, trace.get_tracer_provider())
provider.add_span_processor(span_processor)

registry = CollectorRegistry()
REQUEST_COUNT = Counter(
    "monitoring_request_count",
    "Number of requests served",
    ["endpoint"],
    registry=registry,
)


@app.route("/metrics")
def metrics() -> Response:
    """Return Prometheus metrics."""
    REQUEST_COUNT.labels(endpoint="metrics").inc()
    data = generate_latest(registry)
    return Response(data, mimetype="text/plain")


@app.route("/overview")
def overview() -> Response:
    """Provide a simple system overview."""
    REQUEST_COUNT.labels(endpoint="overview").inc()
    info = {"status": "ok"}
    return jsonify(info)


@app.route("/analytics")
def analytics() -> Response:
    """Return placeholder analytics dashboard data."""
    REQUEST_COUNT.labels(endpoint="analytics").inc()
    data = {"visitors": 0}
    return jsonify(data)


@app.route("/logs")
def logs() -> Response:
    """Return the last few log lines."""
    REQUEST_COUNT.labels(endpoint="logs").inc()
    log_file = Path("monitoring.log")
    lines: Iterable[str]
    if log_file.exists():
        lines = log_file.read_text().splitlines()[-10:]
    else:
        lines = []
    return jsonify({"logs": list(lines)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
