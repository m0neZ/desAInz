FROM python:3.11-slim
RUN apt-get update \
    && apt-get install -y postgresql-client awscli cron \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY scripts/backup.py /app/backup.py
COPY LICENSES /licenses/LICENSES
COPY docker/backup/backup-crontab /etc/cron.d/backup
RUN chmod 0644 /etc/cron.d/backup && crontab /etc/cron.d/backup
CMD ["cron", "-f"]
