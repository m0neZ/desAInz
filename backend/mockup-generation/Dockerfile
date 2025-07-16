FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu20.04

WORKDIR /app

RUN apt-get update && apt-get install -y git python3-pip && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "mockup_generation.celery_app", "worker", "--loglevel=info"]
