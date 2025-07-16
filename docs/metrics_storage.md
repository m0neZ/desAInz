# Metrics Storage with TimescaleDB

This project stores publish latency and scoring metrics in **TimescaleDB** for efficient time-series queries.

1. Run TimescaleDB and configure `METRICS_DB_URL` to point to the instance.
2. The monitoring service uses `TimescaleMetricsStore` to insert `scores` and `publish_latency` records.
3. Downsample data with a continuous aggregate view:

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS latency_hourly
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', timestamp) AS bucket,
       AVG(latency_seconds) AS avg_latency
FROM publish_latency
GROUP BY bucket;
```

Visualize trends in Grafana by connecting to TimescaleDB and building dashboards from the `scores` and `latency_hourly` tables.
