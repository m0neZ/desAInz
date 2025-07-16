# desAInz

This repository contains the desAInz project. Use `scripts/setup_codex.sh` to install dependencies and build the documentation in a Codex environment.

```bash
./scripts/setup_codex.sh
```

Run `scripts/register_schemas.py` after the Kafka and schema registry containers start to register the provided JSON schemas.

## Development helpers

Run the common tasks using the `Makefile`:

```bash
make up    # start services with Docker Compose
make test  # run Python tests
make lint  # run linters for Python and JavaScript
```

## Debugging with VSCode

VSCode launch configurations are provided in `.vscode/launch.json`.
Start the desired configuration from the Run panel to attach the debugger to the FastAPI API or the Next.js admin dashboard.
