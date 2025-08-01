Dagster Orchestrator
====================

This service runs all scheduled workflows. Start it locally with two processes:

.. code-block:: bash

   ./scripts/setup_codex.sh
   ./scripts/run_dagster_webserver.sh
   ./scripts/run_dagster_daemon.sh

The web interface listens on http://localhost:3000.

Run the containers with Docker Compose:

.. code-block:: bash

   docker compose up orchestrator orchestrator-scheduler

For Kubernetes deployments apply the kustomization in ``infrastructure/k8s``:

.. code-block:: bash

   kubectl apply -k infrastructure/k8s/base
