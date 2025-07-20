FROM python:3.11-slim AS builder
WORKDIR /install
RUN pip install --prefix=/usr/local dagster dagster-webserver

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY backend/orchestrator /app/orchestrator
COPY LICENSES /licenses/LICENSES
CMD ["dagster-webserver", "-w", "orchestrator/workspace.yaml", "-h", "0.0.0.0", "-p", "3000"]
