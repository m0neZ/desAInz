FROM python:3.11-slim
WORKDIR /app
COPY scripts/rotate_logs.py /app/rotate_logs.py
COPY LICENSES /licenses/LICENSES
CMD ["python", "/app/rotate_logs.py"]
