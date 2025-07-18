# Log Aggregation with Loki

The monitoring service and all backend applications can send structured log
messages to a Loki instance. Set the ``LOKI_URL`` environment variable to the
Loki HTTP endpoint (e.g. ``http://loki:3100``) and each service will push JSON
logs containing ``correlation_id`` and ``user`` fields. Docker Compose and the
Kubernetes base manifests include a Loki service listening on port ``3100``.
