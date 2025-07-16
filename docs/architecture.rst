Architecture
============

.. mermaid::

   graph TB
       users[Users] --> dashboard[Admin Dashboard]
       dashboard --> api[API Gateway]
       api --> template[Service Template]
       api --> mockup[Mockup Generation]
       api --> scoring[Scoring Engine]
       template --> storage[S3 Storage]
       mockup --> storage
       scoring --> storage

This diagram shows the high-level interaction between the dashboard and the
backend services.

Observability
-------------

All services emit JSON logs containing correlation IDs. Logs are streamed to
CloudWatch when the ``CLOUDWATCH_LOG_GROUP`` environment variable is set. Traces
are exported to Jaeger using OpenTelemetry so requests can be followed across
services.
