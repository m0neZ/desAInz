---
orphan: true
---

# Performance Profiling

Recent profiling efforts added a lightweight middleware which logs request durations for all backend services. Both FastAPI and Flask applications now call `add_profiling` during startup. The middleware records timing for each request using `time.perf_counter` and writes the result to the service log.

During analysis the `analytics` service showed slow responses when aggregating metrics. SQL queries were updated to use database-side aggregation via `SUM` instead of loading entire tables into memory.

## Next Steps
- Monitor logs for high latency endpoints
- Investigate database indexes for frequently queried columns

## Scoring Engine Caching

The ``/score`` endpoint now uses Redis with configurable expiration.
Running ``scripts/benchmark_score.py`` against a local instance showed the
following times for 100 requests:

```
$ python scripts/benchmark_score.py
Uncached: 0.80s for 100 runs
Cached:   0.25s for 100 runs
```

Caching reduces request latency by roughly 3x in this small test.

## Benchmark Automation

The Dagster job `benchmark_score_job` executes
`scripts.benchmark_score.main` on a schedule and persists the results in the
`score_benchmarks` table. Grafana uses the PostgreSQL data source to visualize
these benchmarks over time, allowing quick detection of regressions.

## tRPC Response Caching

The API Gateway now attaches ``ETag`` headers to tRPC responses. When a client
sends ``If-None-Match`` with a previously returned value, the gateway responds
with ``304 Not Modified`` and an empty body. This avoids transferring identical
payloads and improves perceived latency when data has not changed.

## Scaling Strategy

Production workloads run under Kubernetes with [Horizontal Pod Autoscalers](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/).
Each service scales between two and five replicas based on CPU and memory usage.
The `signal-ingestion` deployment also reacts to queue pressure using a custom
`celery_queue_length` metric.  When the average queue length exceeds 30 pending
tasks, additional workers are spawned automatically.

## GPU Slot Metrics

GPU-bound workloads now expose lock usage information through Prometheus.
The context manager `tasks.gpu_slot` updates two metrics:

- ``gpu_slots_in_use`` – a gauge tracking the number of acquired GPU locks.
- ``gpu_slot_acquire_total`` – a counter incremented whenever a slot is obtained.

These metrics appear alongside existing ones on the ``/metrics`` endpoint.

## CDN Configuration

Static assets are distributed through a CloudFront CDN for low latency delivery.
The helper script ``scripts/configure_cdn.sh`` provisions a distribution with a
default TTL of one hour and HTTPS enforced. Refer to the script for exact
settings.

To create a distribution:

```bash
# configure your AWS credentials first
aws configure

# <bucket> and <origin> depend on your setup
./scripts/configure_cdn.sh <bucket> <origin-domain>
```

The command prints a distribution ID which is later required when running
``scripts/invalidate_cache.sh``.
