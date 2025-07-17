# Log Aggregation with Loki

The monitoring service can send structured log messages to a Loki instance. Set
`LOKI_URL` to the Loki HTTP endpoint and the metrics store will push a short log
entry whenever metrics are written. Docker Compose and the Kubernetes base
manifests include a Loki service listening on port `3100`.
