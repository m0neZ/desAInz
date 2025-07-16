# Scoring Engine

This microservice calculates scores for design ideas using multiple factors:
freshness, engagement, novelty, community fit and seasonality. Weighting
parameters are stored in the database and can be updated via the REST API.
Scores are cached in Redis for performance.
