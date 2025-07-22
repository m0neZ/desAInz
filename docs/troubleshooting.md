# Troubleshooting FAQ

## Deployment issues

### Docker containers fail to start

Ensure the required ports (5432, 6379, 9092, 9000, 3000 and 8000) are free. Remove any old containers with:

```bash
docker-compose down -v
```

and try again.

### Missing environment variables

If services exit immediately, verify that your `.env` file contains all variables defined in the example environment files. Copy the appropriate `.env.*.example` file and adjust the values as needed.

### Pending database migrations

Unapplied migrations can block startup. Run `make setup` or invoke `alembic upgrade head` for each backend service before launching the stack.

## Runtime issues

### Documentation build errors

The Sphinx configuration treats warnings as errors. Run the setup script to install required packages and rebuild:

```bash
./scripts/setup_codex.sh
```

### Schemas are not registered

The API relies on Kafka schemas being present. Run:

```bash
python scripts/register_schemas.py
```

### Application ports are unreachable

Check that your firewall allows connections to the exposed ports and verify the containers are listening with `docker ps`.

### Services become unresponsive

Inspect logs using `docker-compose logs <service>` or `kubectl logs <pod>`. Centralized logs are described in [Log Aggregation](logs_with_loki.md).

### Metrics stop updating

Confirm the monitoring service and TimescaleDB are running. See [Metrics Storage](metrics_storage.md) for configuration details.

### Alerts are firing

PagerDuty alerts are triggered for SLA breaches and listing synchronization issues. Review [Monitoring](monitoring.md) for alerting procedures.
