# Log Aggregation with Loki

The monitoring service and all backend applications can send structured log
messages to a Loki instance. Set the ``LOKI_URL`` environment variable to the
Loki HTTP endpoint (e.g. ``http://loki:3100``) and each service will push JSON
logs containing ``correlation_id`` and ``user`` fields. Docker Compose and the
Kubernetes base manifests include a Loki service listening on port ``3100``.
The Helm chart for the monitoring service exposes a ``loki_url`` value which is
templated into the ``LOKI_URL`` environment variable of the container. Update
``values.yaml`` or the ``all-services`` chart to point at your own Loki instance
if needed.

An ``otel-collector`` container is available in all Docker Compose
configurations. Services send traces to this collector by setting the
``OTEL_EXPORTER_OTLP_ENDPOINT`` environment variable to
``http://otel-collector:4318``. The communication protocol can be adjusted with
``OTEL_EXPORTER_OTLP_PROTOCOL`` which defaults to ``http/protobuf``. Both HTTP
``4318`` and gRPC ``4317`` ports are exposed by the collector.

## Local Testing

Run a disposable Loki container and push a test log entry:

```bash
docker run -d --name loki -p 3100:3100 grafana/loki:2.8.2
curl -X POST "http://localhost:3100/loki/api/v1/push" \
  -H 'Content-Type: application/json' \
  -d '{"streams": [{"stream": {"app": "test"}, "values": [["'$(date +%s%N)'", "hello"]]}]}'
```

The message should appear in Loki or Grafana if configured.
