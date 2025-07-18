FROM python:3.11-slim
RUN apt-get update && apt-get install -y postgresql-client awscli && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY scripts/backup.py /app/backup.py
COPY LICENSES /licenses/LICENSES
ENTRYPOINT ["python", "/app/backup.py"]
