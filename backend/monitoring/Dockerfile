FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app/src:/app
COPY LICENSES /licenses/LICENSES
COPY . .
CMD ["python", "-m", "monitoring.main"]
