# desAInz

This repository contains the desAInz project. Use `scripts/setup_codex.sh` to install dependencies and build the documentation in a Codex environment.

```bash
./scripts/setup_codex.sh
```

Run `scripts/register_schemas.py` after the Kafka and schema registry containers
start to register the provided JSON schemas.

Base Kubernetes manifests are available under `infrastructure/k8s`.
