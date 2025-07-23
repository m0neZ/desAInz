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

PgBouncer
---------

PgBouncer provides lightweight connection pooling for PostgreSQL. Each service
reads the ``PGBOUNCER_URL`` environment variable and connects to PgBouncer when
set. If the variable is unset, the connection falls back to ``DATABASE_URL``.

pg\_stat\_statements
--------------------

The :code:`pg_stat_statements` extension tracks execution statistics for all
SQL queries. It must be enabled so that ``scripts.analyze_query_plans`` can
inspect slow statements. Ensure
``shared_preload_libraries`` includes ``pg_stat_statements`` and restart
PostgreSQL. Then run the following once per database:

.. code-block:: sql

   CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

pgvector Extension
------------------

Vector similarity search relies on the `pgvector` extension. Enable it on each
database before applying migrations:

.. code-block:: sql

   CREATE EXTENSION IF NOT EXISTS vector;

HTTP Timeouts
-------------

All services make outbound requests using ``httpx``. The recommended timeout
for these calls is 10 seconds and is exposed as
``backend.shared.http.DEFAULT_TIMEOUT``. Use
``backend.shared.http.get_async_http_client()`` to obtain a shared
``httpx.AsyncClient`` instance cached for the running event loop and
configured with this timeout.
