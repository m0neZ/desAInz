# Makefile with common commands

up:
	docker compose up -d

test:
	python -m pytest -W error

lint:
	python -m flake8
	npm run lint
