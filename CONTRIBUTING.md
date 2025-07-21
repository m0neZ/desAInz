# Contributing

This project uses [pre-commit](https://pre-commit.com/) to automate code quality checks.
To get started:

1. Install the tool:
   ```bash
   pip install pre-commit
   ```
2. Install the git hooks:
   ```bash
   pre-commit install
   ```

Black and Prettier run in formatting mode, so staged files will be automatically
updated.

The hooks enforce Black, flake8, mypy, docformatter, pydocstyle, eslint, prettier, flow and stylelint. Warnings are treated as errors, so commits will fail until issues are fixed.

## CI Lint Commands

The continuous integration workflow runs the following commands and fails on any warnings:

```bash
black --check .
flake8 .
mypy backend --explicit-package-bases --exclude "tests"
npm run lint
npm run flow
```

## Commit Messages

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification. Examples:

```
feat: add scoring endpoint
fix: correct error handling
chore: update dependencies
```

Use these prefixes so the release script can determine the next semantic version and generate the changelog.

## Releasing

Run `./scripts/release.sh <registry>` after your changes are merged. The script updates `CHANGELOG.md`, creates a git tag, builds Docker images and pushes them with the new version number.

## Database Migrations

Migrations for each service live under `backend/shared/db/migrations`. After changing models, generate a new revision:

```bash
alembic -c backend/shared/db/<config>.ini revision -m "add feature" --autogenerate
```

Before merging branches ensure only one revision head exists. If multiple heads are reported by `alembic heads`, create a merge revision:

```bash
alembic -c backend/shared/db/<config>.ini merge -m "merge heads" HEADS
```

Run the migration tests to verify the chain is valid:

```bash
pytest tests/test_migrations.py tests/integration/test_alembic_heads.py
```

## Third-Party Licenses

Generate the bundled `LICENSES` file with:

```bash
python scripts/collect_licenses.py
```

Copy this file into all Docker contexts and ensure each Dockerfile includes:

```Dockerfile
COPY LICENSES /licenses/LICENSES
```

The resulting images must contain `/licenses/LICENSES` in the final layer.
