# desAInz

This repository contains the desAInz project. Use `scripts/setup_codex.sh` to install dependencies and build the documentation in a Codex environment.

```bash
./scripts/setup_codex.sh
```

Run `scripts/register_schemas.py` after the Kafka and schema registry containers
start to register the provided JSON schemas.

PgBouncer connection pooling is available via the `pgbouncer` service in
`docker-compose.yml`. Point `DATABASE_URL` at port `6432` to leverage pooling.
Execute `scripts/analyze_query_plans.py` periodically to inspect query plans and
identify missing indexes.
