# GPU Mockup Generation

The mockup generation service runs inside CUDA-enabled containers. Each
Celery worker is pinned to a specific GPU using the `GPU_WORKER_INDEX`
environment variable. Workers listen on dedicated queues
`gpu-<index>` so Kubernetes can scale them independently.

```bash
# build image and target the first GPU
docker build -f backend/mockup-generation/Dockerfile \
  --build-arg GPU_INDEX=0 -t mockupgen:latest .
```

The provided HorizontalPodAutoscaler manifests scale the deployment
based on CPU, memory and the `celery_queue_length` metric.
