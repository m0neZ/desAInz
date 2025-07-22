# Makefile with common commands

REGISTRY ?= ghcr.io/example
TAG ?= latest
ENV ?= dev

up:
	docker compose -f docker-compose.dev.yml up -d

cdn-up:
	docker compose -f docker-compose.dev.yml up -d cdn-proxy

prod-up:
	docker compose -f docker-compose.prod.yml up -d

test:
	docker compose -f docker-compose.dev.yml -f docker-compose.test.yml up -d
	python -m pytest -n auto -W error -vv
	npm test
	npm run test:e2e
	docker compose -f docker-compose.dev.yml -f docker-compose.test.yml down

lint:
	flake8 .
	mypy backend --explicit-package-bases --exclude "tests"
	pydocstyle .
	docformatter --check --recursive .
	pip-audit -r requirements.txt -r requirements-dev.txt
	npm run lint
	npm run lint:css
	npm run flow

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
