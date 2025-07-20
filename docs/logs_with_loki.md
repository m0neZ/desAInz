# Log Aggregation with Loki

The monitoring service and all backend applications can send structured log
messages to a Loki instance. Set the ``LOKI_URL`` environment variable to the
Loki HTTP endpoint (e.g. ``http://loki:3100``) and each service will push JSON
logs containing ``correlation_id`` and ``user`` fields. Docker Compose and the
Kubernetes base manifests include a Loki service listening on port ``3100``.

An ``otel-collector`` container is available in all Docker Compose
configurations. Services send traces to this collector by setting the
``OTEL_EXPORTER_OTLP_ENDPOINT`` environment variable to
``http://otel-collector:4318``. The communication protocol can be adjusted with
``OTEL_EXPORTER_OTLP_PROTOCOL`` which defaults to ``http/protobuf``. Both HTTP
``4318`` and gRPC ``4317`` ports are exposed by the collector.
