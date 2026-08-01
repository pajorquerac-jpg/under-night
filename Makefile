.PHONY: up down logs migrate migration seed test lint format mobile-install mobile-start

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f api postgres

migrate:
	docker compose run --rm api alembic upgrade head

migration:
	docker compose run --rm api alembic revision --autogenerate -m "$(name)"

seed:
	docker compose run --rm api python scripts/seed.py

test:
	cd apps/api && pytest

lint:
	cd apps/api && ruff check . && mypy app
	cd apps/mobile && npm run lint

format:
	cd apps/api && ruff format .
	cd apps/mobile && npm run format

mobile-install:
	cd apps/mobile && npm install

mobile-start:
	cd apps/mobile && npx expo start
