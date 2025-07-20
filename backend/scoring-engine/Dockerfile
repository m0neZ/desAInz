FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt ./
RUN pip install --prefix=/usr/local --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app/src:/app
COPY --from=builder /usr/local /usr/local
COPY LICENSES /licenses/LICENSES
COPY . .
CMD ["python", "-m", "scoring_engine.app"]
