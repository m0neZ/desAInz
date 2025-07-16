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
