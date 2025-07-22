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

Auth0 manages the signing keys for issued tokens. Rotation of these keys is
handled automatically by Auth0 and requires no action from the services. During
tests or local development, a static `SECRET_KEY` is still used and should be
rotated periodically following the usual secret rotation procedure.

### Automated rotation

The `scripts/rotate_secrets.py` helper generates new random tokens and patches
the corresponding Kubernetes secrets using `kubectl`. A Dagster job executes
this script once per month. The `monthly_secret_rotation_schedule` defined in
`backend.orchestrator.orchestrator.schedules` triggers the job on the first
day of every month at midnight UTC. The run waits for approval via the
`/approvals` API before applying rotations and sends a Slack notification when
complete.

### S3 access key rotation

`scripts/rotate_s3_keys.py` creates new access keys for the configured IAM
user and updates the Kubernetes secret used by the services. The Dagster
`rotate_s3_keys_job` runs monthly. The IAM role executing the script must have
the following permissions:

- `iam:CreateAccessKey`
- `iam:ListAccessKeys`
- `iam:DeleteAccessKey`

## Marketplace webhook signatures

Incoming callbacks to the marketplace publisher include an `X-Signature`
header. The value is an HMAC SHA-256 digest of the raw request body using a
secret unique to each marketplace. Secrets are stored under `secrets/` and are
loaded by the settings module from `/run/secrets` in production. Requests
without a valid signature are rejected with `403 Forbidden`.

## Health endpoints

Each service exposes `/health` and `/ready` for liveness and readiness
checks. `/health` is always public. Access to `/ready` can be restricted by
setting the `ALLOW_STATUS_UNAUTHENTICATED` environment variable to `false`.
When disabled, clients must include an `X-API-Key` header. This allows public
liveness checks while keeping readiness information private.
