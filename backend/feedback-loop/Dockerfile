FROM python:3.11-slim AS builder
WORKDIR /app

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app/src:/app
COPY --from=builder /usr/local /usr/local
COPY LICENSES /licenses/LICENSES
COPY . .
CMD ["python", "-m", "feedback_loop.main"]
