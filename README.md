# desAInz

This repository contains the desAInz project. Use `scripts/setup_codex.sh` to install dependencies and build the documentation in a Codex environment.

```bash
./scripts/setup_codex.sh
```


## Development helpers

Run the common tasks using the `Makefile`:

```bash
make up           # start services with Docker Compose
make test         # run unit and integration tests
make lint         # run all linters and type checkers
make docker-build # build local Docker images
make docker-push  # push images to REGISTRY with TAG
make helm-deploy  # deploy charts with Helm
```

## Type Checking

Run Flow across the repository with:

```bash
npm run flow
```

## Debugging with VSCode

VSCode launch configurations are provided in `.vscode/launch.json`.
Start the desired configuration from the Run panel to attach the debugger to the FastAPI API or the Next.js admin dashboard.

Run `scripts/register_schemas.py` after the Kafka and schema registry containers
start to register the provided JSON schemas.

Base Kubernetes manifests are available under `infrastructure/k8s`.

PgBouncer connection pooling is available via the `pgbouncer` service in
`docker-compose.yml`. Point `DATABASE_URL` at port `6432` to leverage pooling.
Execute `scripts/analyze_query_plans.py` periodically to inspect query plans and
identify missing indexes.

## Configuration and Secrets

Local development uses dotenv files. Copy the `.env.example` in each service to `.env` and adjust the values for your environment. The services automatically load these variables using Pydantic `BaseSettings`.

In production, secrets are stored in HashiCorp Vault or AWS Secrets Manager and surfaced to the containers via Docker secrets or Kubernetes Secrets. The settings modules read from `/run/secrets` if present. Do not rely on `.env` files in production.

See [docs/security.md](docs/security.md) for the rotation procedure.

## Release process

1. Ensure all commits follow the Conventional Commits specification.
2. Run `./scripts/release.sh <registry>` to generate the changelog, tag the release and publish versioned Docker images.
