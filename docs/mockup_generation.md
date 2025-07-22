# GPU Mockup Generation

The mockup generation service runs inside CUDA-enabled containers. Each
Celery worker is pinned to a specific GPU using the `GPU_WORKER_INDEX`
environment variable. Workers listen on dedicated queues `gpu-<index>`
so Kubernetes can scale them independently. Tasks can target a specific
GPU by passing `gpu_index` to the `/generate` endpoint, which will
route them to the corresponding queue.

```bash
# build image and target the first GPU
docker build -f backend/mockup-generation/Dockerfile \
  --build-arg GPU_INDEX=0 -t mockupgen:latest .
```

The provided HorizontalPodAutoscaler manifests scale the deployment
based on CPU, memory and the `celery_queue_length` metric. The number of
concurrent GPU tasks is controlled by the Redis key `gpu_slots`. Update the
key at runtime to change how many workers can acquire a GPU lock:

```bash
redis-cli set gpu_slots 2
```

An example HPA manifest lives in `infrastructure/k8s/examples/gpu-worker-hpa.yaml`
and scales the `mockup-generation` deployment according to queue length.

The metadata generation service uses OpenAI's GPT‑4 model by default. The
model can be changed by setting the `OPENAI_MODEL` environment variable.
