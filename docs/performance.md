# Performance Profiling

Profiling middleware has been added to every FastAPI and Flask service. When the
`ENABLE_PROFILING` environment variable is set to `1`, each request is wrapped in
a `cProfile` session and the statistics are written to `/tmp/profiles`.

This allows capturing per-endpoint CPU usage for further analysis. The middleware
is lightweight and disabled by default to avoid runtime overhead in production.

## Database Optimizations

The `marketplace_publisher` service now retrieves tasks using
`AsyncSession.get` which issues a direct `SELECT` by primary key. Signal
ingestion commits are batched per adapter to reduce transaction overhead.

These changes reduced the average response time of the publish and ingest
endpoints during local testing.
