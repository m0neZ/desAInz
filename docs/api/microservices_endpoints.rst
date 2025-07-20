Microservice Endpoint Overview
==============================

This section lists the HTTP API endpoints for each microservice. The embedded
OpenAPI specifications are generated during the documentation build.

.. toctree::
   :maxdepth: 1

   ../openapi/api-gateway
   ../openapi/analytics
   ../openapi/marketplace-publisher
   ../openapi/monitoring
   ../openapi/optimization
   ../openapi/scoring-engine
   ../openapi/signal-ingestion

Analytics
---------

Example request and response derived from ``tests/test_analytics.py``::

   GET /ab_test_results/1
   -> 200
   {
       "conversions": 8,
       "impressions": 18
   }

   GET /marketplace_metrics/1
   -> 200
   {
       "clicks": 20,
       "purchases": 2,
       "revenue": 40.0
   }

Monitoring
----------

Example interactions from ``tests/test_monitoring.py``::

   GET /health
   -> {"status": "ok"}
   GET /ready
   -> {"status": "ready"}

Optimization
------------

Examples from ``tests/test_api.py``::

   POST /metrics {"cpu_percent": 90, "memory_mb": 2048, "timestamp": "..."}
   -> 200
   GET /optimizations
   -> 200
   GET /recommendations
   -> 200

API Gateway
-----------

Examples based on ``tests/test_api_models.py``::

   GET /models  (with valid Authorization header)
   -> 200
   POST /models/2/default  (with valid Authorization header)
   -> 200


Scoring Engine
--------------

Endpoints verifying the scoring weights can be retrieved and updated. Updating
weights requires the ``X-Weights-Token`` header::

   GET /weights
   -> 200
   {
       "freshness": 0.1,
       "engagement": 0.2,
       "novelty": 0.3,
       "community_fit": 0.2,
       "seasonality": 0.2
   }

   PUT /weights  (with X-Weights-Token header)
   {
       "freshness": 0.5,
       "engagement": 0.1,
       "novelty": 0.2,
       "community_fit": 0.1,
       "seasonality": 0.1
   }
   -> 200
