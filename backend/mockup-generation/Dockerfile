FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt ./
RUN pip install --prefix=/usr/local --no-cache-dir -r requirements.txt

FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu20.04
WORKDIR /app
RUN apt-get update && apt-get install -y git python3-pip && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local /usr/local
COPY LICENSES /licenses/LICENSES
COPY . .

ARG GPU_INDEX=0
ENV GPU_WORKER_INDEX=${GPU_INDEX}
ENV CUDA_VISIBLE_DEVICES=${GPU_INDEX}

COPY start_worker.sh /usr/local/bin/start_worker.sh
CMD ["/usr/local/bin/start_worker.sh"]
