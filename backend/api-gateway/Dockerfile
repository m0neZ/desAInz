FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry export -f requirements.txt --without-hashes --output requirements.txt && \
    pip install --prefix=/usr/local --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app/src:/app
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /usr/local /usr/local
COPY LICENSES /licenses/LICENSES
COPY . .
USER appuser
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "-m", "api_gateway.main"]
