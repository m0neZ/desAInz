# Mockup Generation Service

This service generates design mockups using Stable Diffusion XL. It exposes Celery tasks for asynchronous generation and provides a post-processing pipeline.

## Environment Variables

Copy `.env.example` to `.env` and adjust the values.

Set `USE_COMFYUI=true` to delegate image generation to an external ComfyUI
instance. The service will send workflow JSON to `COMFYUI_URL` (default
`http://localhost:8188`). A compatible Docker image is available at
`ghcr.io/comfyanonymous/comfyui:latest` and must be running alongside the
service when this option is enabled.

### Celery Broker

Set `CELERY_BROKER` to `redis`, `rabbitmq` or `kafka` to choose the task broker.
Additional connection parameters are read from environment variables:

```
CELERY_BROKER=redis          # default
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

CELERY_BROKER=rabbitmq
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

CELERY_BROKER=kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

`CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` may be used to override the
computed connection strings if necessary.
