# desAInz

This repository contains the desAInz project. Use `scripts/setup_codex.sh` to install dependencies and build the documentation in a Codex environment.

```bash
./scripts/setup_codex.sh
```

Run `scripts/register_schemas.py` after the Kafka and schema registry containers
start to register the provided JSON schemas.

## Release process

1. Ensure all commits follow the Conventional Commits specification.
2. Run `./scripts/release.sh <registry>` to generate the changelog, tag the release and publish versioned Docker images.
