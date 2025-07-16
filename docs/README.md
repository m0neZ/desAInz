# Documentation

The `blueprints` folder contains a single comprehensive blueprint for the project.

- [Design Idea Engine Complete Blueprint](blueprints/DesignIdeaEngineCompleteBlueprint.md)
- [Sphinx Documentation](sphinx/index.html)

This document merges the original project summary, system architecture, deployment guide, implementation plan and all earlier blueprint versions into one reference.

## Service Template

The `backend/service-template` directory contains a minimal FastAPI service. The
application loads configuration from environment variables using
`pydantic.BaseSettings`. Variables can be provided via a `.env` file. The
`Settings` class is defined in `src/settings.py` and read on startup.
