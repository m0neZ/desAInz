# Monitoring and Tracing

This project provides optional OpenTelemetry tracing for all backend services. Traces are exported via OTLP and can be collected by an OpenTelemetry Collector.

## Enabling Tracing

1. Set `OTEL_EXPORTER_OTLP_ENDPOINT` to the collector endpoint (e.g. `http://otel-collector:4318`).
2. Optionally set `OTEL_EXPORTER_OTLP_PROTOCOL` to `grpc` or `http/protobuf`.
3. Ensure `OTEL_SDK_DISABLED` is unset or `false`.

With these variables configured, calling `configure_tracing` will send spans to the collector.

## Docker Compose Example

The following override file starts an `otel-collector` container. Launch it alongside the default compose file to enable tracing locally.

```yaml
version: '3.8'
services:
  otel-collector:
    image: otel/opentelemetry-collector:latest
    ports:
      - "4317:4317"
      - "4318:4318"
```

Run:

```bash
docker compose -f docker-compose.yml -f docker-compose.tracing.yml up -d otel-collector
```
