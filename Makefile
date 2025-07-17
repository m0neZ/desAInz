# Makefile with common commands

REGISTRY ?= ghcr.io/example
TAG ?= latest
ENV ?= dev

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

docker-build:
        ./scripts/build-images.sh

docker-push:
        ./scripts/push-images.sh $(REGISTRY) $(TAG)

helm-deploy:
        ./scripts/helm_deploy.sh $(REGISTRY) $(TAG) $(ENV)

ci: lint test docker-build
