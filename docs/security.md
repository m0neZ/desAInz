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
