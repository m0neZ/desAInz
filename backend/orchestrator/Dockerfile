FROM python:3.11-slim
WORKDIR /app
COPY backend/orchestrator /app/orchestrator
COPY LICENSES /licenses/LICENSES
RUN pip install dagster dagster-webserver
CMD ["dagster-webserver", "-w", "orchestrator/workspace.yaml", "-h", "0.0.0.0", "-p", "3000"]
