# Local Quick Start

Follow these steps to run desAInz on your workstation.

## 1. Clone the repository

```bash
git clone https://github.com/your-org/desAInz.git
cd desAInz
```

## 2. Install dependencies

Use the provided setup script to install Python and Node packages and build the documentation.

```bash
./scripts/setup_codex.sh
```

For faster repeated runs, activate a virtual environment stored outside the
repository before executing the script:

```bash
python -m venv ~/.cache/desainz_venv
source ~/.cache/desainz_venv/bin/activate
./scripts/setup_codex.sh
```

## 3. Launch the stack

Start the application and its services with Docker Compose.

```bash
docker-compose up -d
```

Once all containers are healthy, register the Kafka schemas.

```bash
python scripts/register_schemas.py
```

## 4. Verify the application

Check that the API and frontend respond.

```bash
curl http://localhost:8000/health
curl http://localhost:8000/recommendations
curl http://localhost:3000
```

You can stop the stack with:

```bash
docker-compose down
```
