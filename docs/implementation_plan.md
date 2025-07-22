# Implementation Plan

This document outlines the high-level milestones for desAInz. It references the [Design Idea Engine Complete Blueprint](blueprints/DesignIdeaEngineCompleteBlueprint.md) for additional context.

## Milestones

1. **Analysis & Planning** – finalize technology choices and architecture diagrams.
2. **Core Services** – implement Signal Ingestion, Data Storage and Scoring Engine APIs.
3. **AI Integration** – add the Prompt Builder, mock-up generation and listing draft creation.
4. **Frontend Dashboard** – build the Next.js admin dashboard.
5. **Marketplace Integration** – enable one-click publish and gather performance data.
6. **Monitoring & Optimization** – add observability, auto‑scaling and brand‑safety checks.
7. **Testing & Deployment** – run automated tests and deploy via Docker or Kubernetes.

These milestones mirror the roadmap in the blueprint while providing a concise overview for contributors.

## Selected Technologies

The project uses a lightweight stack chosen for cost efficiency and ease of deployment.
The concrete service definitions live in the `docker-compose*.yml` files and the
Kubernetes manifests under `infrastructure/k8s/`.

### Database

- **PostgreSQL 15 with pgvector** – see the ``postgres`` service in
  [`../docker-compose.yml`](../docker-compose.yml). Connection details are
  templated in [`../infrastructure/k8s/base/configmap.yaml`](../infrastructure/k8s/base/configmap.yaml).
- **Redis** for caching and as a Celery broker – defined as ``redis`` in the
  compose files.
- **MinIO** object storage – provided by the ``minio`` service.

### Message Broker

- **Kafka** with **Zookeeper** and **Schema Registry** – see the ``kafka``,
  ``zookeeper`` and ``schema-registry`` services in `docker-compose.yml`. The
  manifests in `infrastructure/k8s/base/` reference the external broker via
  environment variables.

### AI Components

- **OpenAI GPT‑4** and **Stable Diffusion XL** – used by the
  ``mockup-generation`` service defined in [`../docker-compose.yml`](../docker-compose.yml)
  and [`../infrastructure/k8s/base/ai-mockup-generation-deployment.yaml`](../infrastructure/k8s/base/ai-mockup-generation-deployment.yaml).
- **Scoring Engine** – container named ``scoring-engine`` in the compose file
  with a matching deployment manifest.

### CI/CD

 - **GitHub Actions** – workflows under `../.github/workflows` run linting,
   testing and deployment.
- **Helm** and **Kustomize** – `pipeline.yml` deploys the manifests from
  `infrastructure/k8s/` using Helm.

### Monitoring

- **Prometheus**, **Grafana** and **Loki** – available through the ``prometheus``,
  ``grafana`` and ``loki`` services in [`../docker-compose.yml`](../docker-compose.yml)
  and corresponding manifests in `infrastructure/k8s/base/`.
- **OpenTelemetry Collector** – the ``otel-collector`` service in
  [`../docker-compose.tracing.yml`](../docker-compose.tracing.yml) aggregates traces from all services.
