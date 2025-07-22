# Configuration

This project uses environment variables for all runtime configuration. The
example files `.env.dev.example`, `.env.staging.example` and
`.env.prod.example` provide sample values for each deployment stage. Copy the
appropriate file to `.env` and adjust the values before running services
locally or in CI. In production, sensitive variables are mounted from Docker or
Kubernetes secrets under `/run/secrets` and loaded automatically by the
application settings classes.
See the blueprint environment variables section in `blueprints/DesignIdeaEngineCompleteBlueprint.md` for a complete example of the `.env` layout for each service.


| Variable | Description |
| --- | --- |
| `DATABASE_URL` | Database connection string |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | Secret key for cryptographic signing |
| `AUTH0_DOMAIN` | Domain of the Auth0 tenant used for authentication |
| `AUTH0_CLIENT_ID` | Client identifier issued by Auth0 |
| `OPENAI_API_KEY` | OpenAI API authentication token used for image and listing generation |
| `STABILITY_AI_API_KEY` | Stability AI API token |
| `FALLBACK_PROVIDER` | `stability` or `dall-e` |
| `HUGGINGFACE_TOKEN` | Hugging Face API token for Claude-based listing generation |
| `S3_ENDPOINT` | URL of the object storage service |
| `S3_ACCESS_KEY` | Object storage access key |
| `S3_SECRET_KEY` | Object storage secret key |
| `S3_BUCKET` | Bucket name for storing assets |
| `S3_BASE_URL` | Public base URL for accessing stored objects |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker list |
| `SCHEMA_REGISTRY_URL` | Schema Registry endpoint |
| `SCHEMA_REGISTRY_TOKEN` | Authentication token for the schema registry |
| `LOG_LEVEL` | Logging verbosity |
| `APPROVAL_SERVICE_URL` | Base URL of the manual approval service |
| `ALLOWED_ORIGINS` | Comma separated whitelist of origins for CORS |
| `ALLOW_STATUS_UNAUTHENTICATED` | Set to `false` to require an API key for `/ready` |
| `WEIGHTS_TOKEN` | Token required for updating scoring weights |
| `ENABLED_ADAPTERS` | Comma separated list of ingestion adapters to run; if unset all adapters are used |
| `PAGERDUTY_ROUTING_KEY` | Integration key for sending PagerDuty incidents |
| `ENABLE_PAGERDUTY` | Set to `true` to enable PagerDuty notifications |
| `SLA_ALERT_COOLDOWN_MINUTES` | Minimum minutes between SLA alerts |
| `DEDUP_ERROR_RATE` | Probability of false positives in the Bloom filter |
| `DEDUP_CAPACITY` | Estimated maximum number of entries in the Bloom filter |
| `DEDUP_TTL` | Time-to-live in seconds for deduplication keys |
| `PUBLISHER_METRICS_INTERVAL_MINUTES` | Interval for fetching publisher metrics |
| `WEIGHT_UPDATE_INTERVAL_MINUTES` | Interval for updating scoring weights |
| `HTTP_RETRIES` | Number of retry attempts for outgoing HTTP calls |
| `SENTRY_DSN` | Sentry Data Source Name for error reporting |
| `METRICS_DB_URL` | TimescaleDB connection string for storing metrics |
| `API_GATEWAY_WS_INTERVAL_MS` | WebSocket polling interval for API Gateway |
| `CELERY_BROKER` | Celery broker backend (e.g., `redis`) |
| `REDIS_HOST` | Redis host for Celery |
| `REDIS_PORT` | Redis port for Celery |
| `REDIS_DB` | Redis database index for Celery |
| `RABBITMQ_HOST` | RabbitMQ host for Celery |
| `RABBITMQ_PORT` | RabbitMQ port |
| `RABBITMQ_USER` | RabbitMQ username |
| `RABBITMQ_PASSWORD` | RabbitMQ password |
| `INSTAGRAM_TOKEN` | Instagram Graph API token |
| `INSTAGRAM_USER_ID` | Instagram user id to fetch posts from |
| `INSTAGRAM_FETCH_LIMIT` | Number of Instagram posts to retrieve |
| `REDDIT_USER_AGENT` | User agent string for Reddit API |
| `REDDIT_FETCH_LIMIT` | Number of Reddit posts to retrieve |
| `YOUTUBE_API_KEY` | YouTube Data API key |
| `YOUTUBE_FETCH_LIMIT` | Number of YouTube videos to retrieve |
| `TIKTOK_VIDEO_URLS` | Comma separated list of TikTok video URLs |
| `TIKTOK_FETCH_LIMIT` | Number of TikTok videos to retrieve |
| `NOSTALGIA_QUERY` | Search query for Nostalgia data |
| `NOSTALGIA_FETCH_LIMIT` | Number of Nostalgia items to retrieve |
| `EVENTS_COUNTRY_CODE` | Event API country code |
| `EVENTS_FETCH_LIMIT` | Number of events to retrieve |
