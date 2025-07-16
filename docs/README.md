# Documentation

The `blueprints` folder contains the full system blueprint.

- [Design Idea Engine Complete Blueprint](blueprints/DesignIdeaEngineCompleteBlueprint.md)
- [Sphinx Documentation](sphinx/index)
- [Configuration](configuration.md)
- [Metrics Storage](metrics_storage.md)

The `scripts` directory provides helper scripts for setting up storage and CDN resources:

- `setup_storage.sh` – create the S3/MinIO bucket structure
- `configure_cdn.sh` – create a CloudFront distribution
- `invalidate_cache.sh` – invalidate CDN caches when mockups change
- Base Kubernetes manifests can be found in `infrastructure/k8s` with instructions for
  customizing them for local Minikube testing.
  This document merges the original project summary, system architecture, deployment guide, implementation plan and all earlier blueprint versions into one reference.

## Service Template

The `backend/service-template` directory contains a minimal FastAPI service. The
application loads configuration from environment variables using
`pydantic.BaseSettings`. Variables can be provided via a `.env` file. The
`Settings` class is defined in `src/settings.py` and read on startup.

## Load Testing

Load tests use [Locust](https://locust.io/) and live in the `load_tests`
directory. To exercise the endpoints locally, start the services you want to
benchmark and run `scripts/run_load_tests.sh`. Continuous integration executes
the same script via the `loadtest` workflow.
