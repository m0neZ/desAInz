# Security and Secret Management

This project relies on environment variables for configuration.

## Local development

- Copy `.env.example` files to `.env` inside each service directory.
- Adjust the values for your local setup.
- The applications load these variables automatically via `pydantic.BaseSettings`.
- For a production-like setup with Docker Compose, place sensitive values in
  files under `secrets/` and reference them as Docker secrets.

## Production

- Secrets are stored in HashiCorp Vault or AWS Secrets Manager and exposed to
  the containers using Kubernetes Secrets.
- Deployment manifests mount the secrets under `/run/secrets`.
- `.env` files are **not** used in production.

## Secret rotation procedure

1. Create a new version of the secret in the secret manager.
2. Update the deployment configuration to reference the new version.
3. Deploy to a staging environment and verify the rollout.
4. Promote the secret to production after validation.
5. Remove the previous version when all services consume the new secret.

### JWT secret rotation

The `SECRET_KEY` used to sign JWT tokens is loaded from `/run/secrets` in
production. To rotate it safely:

1. Deploy the new secret alongside the old one and update the `secret_key`
   environment variable.
2. Insert all active token identifiers into the `revoked_tokens` table so old
   credentials are rejected.
3. Redeploy the services to pick up the new secret and remove the old one when
   all clients have refreshed their tokens.

### Automated rotation

The ``scripts/rotate_secrets.py`` helper generates new random tokens and patches
the corresponding Kubernetes secrets using ``kubectl``. A Dagster job executes
this script once per month. The ``monthly_secret_rotation_schedule`` defined in
``backend.orchestrator.orchestrator.schedules`` triggers the job on the first
day of every month at midnight UTC.
