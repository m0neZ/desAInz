# Monitoring and Tracing

This project provides optional OpenTelemetry tracing for all backend services. Traces are exported via OTLP and can be collected by an OpenTelemetry Collector.

## Enabling Tracing

1. Set `OTEL_EXPORTER_OTLP_ENDPOINT` to the collector endpoint (e.g. `http://otel-collector:4318`).
2. Optionally set `OTEL_EXPORTER_OTLP_PROTOCOL` to `grpc` or `http/protobuf`.
3. Ensure `OTEL_SDK_DISABLED` is unset or `false`.

With these variables configured, calling `configure_tracing` will send spans to the collector.

## Error Tracking

All backend services support error reporting via Sentry. Set the `SENTRY_DSN` environment variable in the service's `.env` file to enable capturing exceptions. The example dotenv files under `backend/*` include this variable so you can populate it with your project DSN.

## Docker Compose Example

The following override file starts an `otel-collector` container. Launch it alongside the default compose file to enable tracing locally.

```yaml
version: '3.8'
services:
  otel-collector:
    image: otel/opentelemetry-collector:latest
    ports:
      - '4317:4317'
      - '4318:4318'
```

Run:

```bash
docker compose -f docker-compose.yml -f docker-compose.tracing.yml up -d otel-collector
```

## Grafana Dashboards

Prebuilt dashboard JSON files reside in `infrastructure/grafana/dashboards`.
Import them into Grafana via **Dashboards → Import** and select the
TimescaleDB data source when prompted. Dashboards are automatically
loaded when deploying via Helm because `grafana.sidecar.dashboards` is
enabled.

Dashboards include:

- `latency.json`
- `queue_length.json`
- `resource_usage.json`
- `optimization.json`
- `service_health.json`

## Prometheus Scrape Configuration

Prometheus is configured through `docker/prometheus/prometheus.yml`. Each service exposes metrics on `/metrics` and the file defines one scrape job per service:

```yaml
scrape_configs:
  - job_name: 'monitoring'
    static_configs:
      - targets: ['monitoring:8000']
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:8000']
  - job_name: 'mockup-generation'
    static_configs:
      - targets: ['mockup-generation:8000']
  - job_name: 'scoring-engine'
    static_configs:
      - targets: ['scoring-engine:5002']
  - job_name: 'marketplace-publisher'
    static_configs:
      - targets: ['marketplace-publisher:8000']
  - job_name: 'signal-ingestion'
    static_configs:
      - targets: ['signal-ingestion:8000']
  - job_name: 'feedback-loop'
    static_configs:
      - targets: ['feedback-loop:8000']
  - job_name: 'orchestrator'
    static_configs:
      - targets: ['orchestrator:3000']
```

## PagerDuty Alerts

Set `PAGERDUTY_ROUTING_KEY` and `ENABLE_PAGERDUTY=true` in the environment to enable alerting. The monitoring service triggers alerts when the average publish latency breaches the configured SLA and when listing synchronization detects issues.
