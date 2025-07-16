# Monitoring Service

This microservice exposes Prometheus metrics and provides simple endpoints for
system overview, analytics, and log retrieval. It also integrates
OpenTelemetry tracing.

## Endpoints

- `/metrics` &mdash; Prometheus metrics.
- `/overview` &mdash; basic system status.
- `/analytics` &mdash; placeholder analytics dashboard data.
- `/logs` &mdash; last few log lines.
