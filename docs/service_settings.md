# Recommended Service Settings

This document summarizes recommended environment variables for each microservice. The values are suitable for a small deployment and can be adjusted as workloads grow.

## API Gateway

- `API_GATEWAY_WS_INTERVAL_MS=1000`

## Signal Ingestion

- `INGEST_INTERVAL_MINUTES=60`
- `ADAPTER_RATE_LIMIT=5`

## Scoring Engine

- `DB_POOL_SIZE=5`

## Mockup Generation

- `GPU_WORKER_INDEX=0`
- `GPU_WORKER_CONCURRENCY=1`

## Marketplace Publisher

- `PUBLISHER_METRICS_INTERVAL_MINUTES=15`

These defaults keep resource usage low while providing responsive APIs. Increase values gradually when scaling services in production.
