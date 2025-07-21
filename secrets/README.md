Store sensitive values in files within this directory for use with Docker Compose.
For example, place your OpenAI API key in `openai_api_key.txt` and reference it as a Docker secret.

The marketplace publisher reads webhook secrets from this directory. Create the
following files with strong random values:

- `WEBHOOK_SECRET_REDBUBBLE`
- `WEBHOOK_SECRET_AMAZON_MERCH`
- `WEBHOOK_SECRET_ETSY`
- `WEBHOOK_SECRET_SOCIETY6`
- `WEBHOOK_SECRET_ZAZZLE`

Mount them under `/run/secrets` when deploying the service.
