# Troubleshooting FAQ

## Docker containers fail to start

Ensure the required ports (5432, 6379, 9092, 9000, 3000 and 8000) are free. Remove any old containers with:

```bash
docker-compose down -v
```

and try again.

## Documentation build errors

The Sphinx configuration treats warnings as errors. Run the setup script to install required packages and rebuild:

```bash
./scripts/setup_codex.sh
```

## Schemas are not registered

The API relies on Kafka schemas being present. Run:

```bash
python scripts/register_schemas.py
```

## Application ports are unreachable

Check that your firewall allows connections to the exposed ports and verify the containers are listening with `docker ps`.

