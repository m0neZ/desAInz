# Performance Profiling

This project now includes lightweight profiling middleware for both FastAPI and Flask services.

## Middleware

`backend.shared.profiling` exposes `add_fastapi_profiler` and `add_flask_profiler`.
These helpers measure request duration in milliseconds and log the value with
basic request metadata.

The profiling middleware has been enabled in each service entrypoint. Logs can be
aggregated to identify slow endpoints.

## Optimized Queries

The analytics service previously fetched all rows to compute aggregates. Queries
now use SQL `SUM` functions, reducing memory usage and latency.

## Next Steps

- Review logs for endpoints exceeding expected latency.
- Continue refining SQL statements or add indexes based on observed hotspots.
