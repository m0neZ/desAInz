FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY LICENSES /licenses/LICENSES
COPY . .
CMD ["python", "-m", "scoring_engine.app"]
