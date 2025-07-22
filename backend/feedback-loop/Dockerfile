FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/usr/local --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app:/app/backend
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /usr/local /usr/local
COPY backend/feedback-loop/feedback_loop ./feedback_loop
COPY backend/shared ./backend/shared
COPY LICENSES /licenses/LICENSES
USER appuser
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "-m", "feedback_loop.main"]
