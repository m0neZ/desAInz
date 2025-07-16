# desAInz

This repository contains the desAInz project. Use `scripts/setup_codex.sh` to install dependencies and build the documentation in a Codex environment.

```bash
./scripts/setup_codex.sh
```

Run `scripts/register_schemas.py` after the Kafka and schema registry containers
start to register the provided JSON schemas.

## Configuration and Secrets

Local development uses dotenv files. Copy the `.env.example` in each service to `.env` and adjust the values for your environment. The services automatically load these variables using Pydantic `BaseSettings`.

In production, secrets are stored in HashiCorp Vault or AWS Secrets Manager and injected into the running services by the deployment manifests. Do not rely on `.env` files in production.

See [docs/security.md](docs/security.md) for the rotation procedure.
