Scripts Reference
=================

The ``scripts`` directory provides small utilities for deploying, maintaining and
troubleshooting the desAInz environment. Each script can be run from the project
root. Examples below show the basic command structure.

Python utilities
----------------

.. list-table::
   :header-rows: 1

   * - Script
     - Purpose
     - Example
   * - ``analyze_query_plans.py``
     - Inspect ``pg_stat_statements`` and suggest indexes.
     - ``python scripts/analyze_query_plans.py``
   * - ``apply_s3_lifecycle.py``
     - Configure bucket lifecycle rules.
     - ``python scripts/apply_s3_lifecycle.py <bucket> [storage-class]``
   * - ``approve_job.py``
     - Approve Dagster runs from the approval service.
     - ``python scripts/approve_job.py <run_id>``
   * - ``backup.py``
     - Dump the PostgreSQL database to S3.
     - ``python scripts/backup.py``
   * - ``benchmark_score.py``
     - Compare scoring latency with and without caching.
     - ``python scripts/benchmark_score.py``
   * - ``benchmark_mockup.py``
     - Measure latency for generating mock-ups.
     - ``python scripts/benchmark_mockup.py``
   * - ``benchmark_metrics_store.py``
     - Compare metric insertion with and without connection pooling.
     - ``python scripts/benchmark_metrics_store.py``
   * - ``cli.py``
     - Entry point exposing ingestion and publishing helpers.
     - ``python scripts/cli.py --help``
   * - ``collect_licenses.py``
     - Gather third‑party license information.
     - ``python scripts/collect_licenses.py``
   * - ``collect_metrics.py``
     - Forward resource usage metrics to monitoring.
     - ``python scripts/collect_metrics.py``
   * - ``daily_summary.py``
     - Produce a JSON activity report.
     - ``./scripts/daily_summary.py``
   * - ``generate_openapi.py``
     - Build OpenAPI specs for all services.
     - ``python scripts/generate_openapi.py``
   * - ``listing_sync.py``
     - Sync marketplace listing states.
     - ``python scripts/listing_sync.py``
   * - ``maintenance.py``
     - Scheduled cleanup tasks executed by Dagster.
     - ``python scripts/maintenance.py``
   * - ``manage_spot_instances.py``
     - Manage AWS spot nodes.
     - ``python scripts/manage_spot_instances.py maintain --count 2``
   * - ``register_schemas.py``
     - Upload JSON schemas to the registry.
     - ``python scripts/register_schemas.py``
   * - ``review_monthly_costs.py``
     - Parse cost reports for anomalies.
     - ``python scripts/review_monthly_costs.py``
   * - ``rotate_logs.py``
     - Archive and prune log files.
     - ``python scripts/rotate_logs.py``
   * - ``rotate_s3_keys.py``
     - Generate new S3 access keys and update secrets.
     - ``python scripts/rotate_s3_keys.py``
   * - ``rotate_secrets.py``
     - Rotate application credentials in Kubernetes.
     - ``python scripts/rotate_secrets.py``
   * - ``run_dagster_webserver.py``
     - Start the Dagster web UI locally.
     - ``python scripts/run_dagster_webserver.py``
   * - ``run_integration_tests.py``
     - Execute integration tests with strict settings.
     - ``python scripts/run_integration_tests.py``
   * - ``setup_codex.py``
     - Prepare dependencies in the Codex environment.
     - ``python scripts/setup_codex.py``
   * - ``update_openapi_changelog.py``
     - Update the changelog after specs change.
     - ``python scripts/update_openapi_changelog.py``
   * - ``wait_for_services.py``
     - Block until dependencies respond on their ports. Use ``--max-wait`` to
       control the timeout.
     - ``python scripts/wait_for_services.py --max-wait 60``

Shell utilities
---------------

``build-images.sh`` builds Docker images using Buildx::

   ./scripts/build-images.sh

``configure_cdn.sh`` creates a CloudFront distribution::

   ./scripts/configure_cdn.sh <bucket>

``deploy.sh`` performs a blue‑green deployment with traffic shifting and
automatic rollback::

   ./scripts/deploy.sh orchestrator ghcr.io/example/orchestrator:latest prod

``helm_deploy.sh`` installs services via Helm::

   ./scripts/helm_deploy.sh ghcr.io/example latest prod

``invalidate_cache.sh`` removes stale CDN objects::

   ./scripts/invalidate_cache.sh

``load-env.sh`` loads variables from a file::

   ./scripts/load-env.sh .env

``push-images.sh`` tags and pushes Docker images::

   ./scripts/push-images.sh ghcr.io/example latest

``release.sh`` bumps versions and pushes images::

   ./scripts/release.sh ghcr.io/example

``rotate_logs.sh`` archives old log files::

   ./scripts/rotate_logs.sh

``run-integration-tests.sh`` calls the Python test runner::

   ./scripts/run-integration-tests.sh

``run_dagster_webserver.sh`` starts the Dagster webserver::

   ./scripts/run_dagster_webserver.sh

``run_load_tests.sh`` executes Locust benchmarks::

   ./scripts/run_load_tests.sh

``setup_codex.sh`` installs all dependencies::

   ./scripts/setup_codex.sh

``setup_storage.sh`` provisions S3 or MinIO buckets::

   ./scripts/setup_storage.sh

``smoke_compose.sh`` runs a short docker-compose health check::

   ./scripts/smoke_compose.sh

``sync_staging_secrets.sh`` copies production secrets to staging::

   ./scripts/sync_staging_secrets.sh

``validate_migrations.sh`` ensures Alembic has a single head and no branches::

   ./scripts/validate_migrations.sh

``wait-for-services.sh`` waits until local services are ready::

   ./scripts/wait-for-services.sh

Other files
-----------

``exit_on_warnings.js`` causes Node processes to fail on warnings.
Use it with ``node --require ./scripts/exit_on_warnings.js <app.js>``.

The ``tests`` directory under ``scripts`` contains integration tests for the
helper utilities.
