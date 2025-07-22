FROM python:3.11-slim AS builder
WORKDIR /install
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/usr/local dagster dagster-webserver

FROM python:3.11-slim
WORKDIR /app
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /usr/local /usr/local
COPY backend/orchestrator /app/orchestrator
COPY LICENSES /licenses/LICENSES
USER appuser
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:3000/ || exit 1
CMD ["dagster-webserver", "-w", "orchestrator/workspace.yaml", "-h", "0.0.0.0", "-p", "3000"]
