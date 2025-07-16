---
orphan: true
---

# Performance Profiling

Recent profiling efforts added a lightweight middleware which logs request durations for all backend services. Both FastAPI and Flask applications now call `add_profiling` during startup. The middleware records timing for each request using `time.perf_counter` and writes the result to the service log.

During analysis the `analytics` service showed slow responses when aggregating metrics. SQL queries were updated to use database-side aggregation via `SUM` instead of loading entire tables into memory.

## Next Steps
- Monitor logs for high latency endpoints
- Investigate database indexes for frequently queried columns
