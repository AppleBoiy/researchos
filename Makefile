.PHONY: up down build logs shell db-shell migrate test test-unit test-property lint fmt

# Docker Compose
up:
	docker compose up

up-d:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f api

# Shells
shell:
	docker compose exec api bash

db-shell:
	docker compose exec db psql -U researchos -d researchos

# Migrations
migrate:
	docker compose exec api alembic upgrade head

migration:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

# Tests (run inside container)
test:
	docker compose exec api pytest --cov=app --cov-report=term-missing

test-unit:
	docker compose exec api pytest tests/unit/ -v

test-property:
	docker compose exec api pytest tests/property/ -v

# Local tests (requires local venv)
test-local:
	FLASK_ENV=testing pytest --cov=app --cov-report=term-missing

# Lint / format
lint:
	ruff check app/ tests/

fmt:
	ruff format app/ tests/
