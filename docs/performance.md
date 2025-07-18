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

## Scaling Strategy

Production workloads run under Kubernetes with [Horizontal Pod Autoscalers](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/).
Each service scales between two and five replicas based on CPU and memory usage.
The `signal-ingestion` deployment also reacts to queue pressure using a custom
`celery_queue_length` metric.  When the average queue length exceeds 30 pending
tasks, additional workers are spawned automatically.
