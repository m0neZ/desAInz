# Makefile with common commands

up:
	docker compose up -d

test:
	python -m pytest -W error

lint:
	python -m flake8
	npm run lint

setup:
	alembic -c backend/shared/db/alembic_api_gateway.ini upgrade head
	alembic -c backend/shared/db/alembic_scoring_engine.ini upgrade head
	alembic -c backend/shared/db/alembic_marketplace_publisher.ini upgrade head
	alembic -c backend/shared/db/alembic_signal_ingestion.ini upgrade head
