FROM postgres:15
RUN apt-get update \
    && apt-get install -y postgresql-15-pgvector \
    && rm -rf /var/lib/apt/lists/*

# Expose Postgres port
EXPOSE 5432

HEALTHCHECK --interval=10s --retries=5 CMD pg_isready -U "$POSTGRES_USER"
