FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt ./
RUN pip install --prefix=/usr/local --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app:/app/backend
COPY --from=builder /usr/local /usr/local
COPY backend/feedback-loop/feedback_loop ./feedback_loop
COPY backend/shared ./backend/shared
COPY LICENSES /licenses/LICENSES
CMD ["python", "-m", "feedback_loop.main"]
