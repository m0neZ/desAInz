# Scoring Engine

This microservice calculates scores for design ideas using multiple factors:
freshness, engagement, novelty, community fit and seasonality. Weighting
parameters are stored in the database and can be updated via the REST API.
Scores are cached in Redis for performance.

## Environment Variables

Copy `.env.example` to `.env` and adjust the values.

`METRICS_DB_URL` points the service at a TimescaleDB instance for storing score
metrics.
