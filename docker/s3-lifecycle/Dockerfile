FROM python:3.11-slim
RUN apt-get update \
    && apt-get install -y awscli cron \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY scripts/apply_s3_lifecycle.py /app/apply_s3_lifecycle.py
COPY LICENSES /licenses/LICENSES
COPY docker/s3-lifecycle/s3lifecycle-crontab /etc/cron.d/s3lifecycle
RUN chmod 0644 /etc/cron.d/s3lifecycle && crontab /etc/cron.d/s3lifecycle
CMD ["cron", "-f"]
