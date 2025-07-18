# Configuration

This project uses environment variables for all runtime configuration. The
example files `.env.dev.example`, `.env.staging.example` and
`.env.prod.example` provide sample values for each deployment stage. Copy the
appropriate file to `.env` and adjust the values before running services
locally or in CI. In production, sensitive variables are mounted from Docker or
Kubernetes secrets under `/run/secrets` and loaded automatically by the
application settings classes.

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | Database connection string |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | Secret key for cryptographic signing |
| `OPENAI_API_KEY` | OpenAI API authentication token |
| `STABILITY_AI_API_KEY` | Stability AI API token |
| `FALLBACK_PROVIDER` | `stability` or `dall-e` |
| `HUGGINGFACE_TOKEN` | Hugging Face API token |
| `S3_ENDPOINT` | URL of the object storage service |
| `S3_ACCESS_KEY` | Object storage access key |
| `S3_SECRET_KEY` | Object storage secret key |
| `S3_BUCKET` | Bucket name for storing assets |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker list |
| `SCHEMA_REGISTRY_URL` | Schema Registry endpoint |
| `LOG_LEVEL` | Logging verbosity |
| `APPROVE_PUBLISHING` | Require publishing approval flag |
