# Feedback Loop Service

This service manages user feedback processing and periodic weight updates.

## Environment Variables

Copy `.env.example` to `.env` and adjust the values for your environment.

## Scheduler lifecycle

The service creates a single APScheduler instance during application startup.
The scheduler runs background ingestion and weight update jobs and is stopped
gracefully when the FastAPI application shuts down.

## API Endpoints

All endpoints require a Bearer token obtained from the API gateway. Event
tracking endpoints ``/impression`` and ``/conversion`` require the ``editor``
role while ``/allocation`` and ``/stats`` require ``admin`` privileges.
