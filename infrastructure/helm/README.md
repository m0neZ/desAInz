# Helm Charts

This directory contains Helm charts for the Design Idea Engine microservices.
Each microservice can be deployed independently. Environment specific values
files are provided for development, staging and production deployments.

## Microservices

- Signal Ingestion
- Data Storage
- Scoring Engine
- AI Mock-up Generation
- Marketplace Publisher
- Feedback Loop
- Orchestrator & CI/CD

## Usage

Ensure you have a Kubernetes cluster and Helm installed. Deploy a service using:

```bash
helm install <release-name> ./<microservice> -f ./<microservice>/values-<env>.yaml
```

Replace `<microservice>` with one of the service directories above and `<env>`
with `dev`, `staging` or `prod`.

### Mirroring Production in Staging

Use `scripts/sync_staging_secrets.sh` to copy production secrets to the staging namespace so that staging closely matches the production environment:

```bash
./scripts/sync_staging_secrets.sh prod staging
```

Deploy the services with the staging values files to complete the mirror.
