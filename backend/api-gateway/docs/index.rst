API Gateway
===========

.. automodule:: api_gateway.main
   :members:

Metrics
-------

Prometheus metrics are exposed at ``/metrics``.

Compression
-----------

Responses larger than 1000 bytes are compressed using Brotli with a gzip
fallback for clients that do not advertise ``br`` support.

Environment Variables
---------------------

``API_GATEWAY_WS_INTERVAL_MS``
    Interval in milliseconds between WebSocket metric updates.
