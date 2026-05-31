COMPOSE := docker compose
BACKEND_DIR := backend

.PHONY: help
help:
	@printf "Available targets:\n"
	@printf "  make dev              Start API, worker, Postgres, and Redis\n"
	@printf "  make down             Stop local services\n"
	@printf "  make logs             Tail local service logs\n"
	@printf "  make sync             Create/update the backend uv environment\n"
	@printf "  make migrate          Run Alembic migrations\n"
	@printf "  make revision MSG=... Create a new Alembic revision\n"
	@printf "  make test             Run backend tests in Docker\n"
	@printf "  make test-local       Run backend tests on the host\n"
	@printf "  make shell            Open a shell in the API container\n"

.PHONY: dev
dev:
	$(COMPOSE) up --build api worker postgres redis

.PHONY: down
down:
	$(COMPOSE) down

.PHONY: logs
logs:
	$(COMPOSE) logs -f api worker postgres redis

.PHONY: sync
sync:
	cd $(BACKEND_DIR) && uv sync --dev

.PHONY: migrate
migrate:
	$(COMPOSE) run --rm api uv run alembic upgrade head

.PHONY: revision
revision:
	@test -n "$(MSG)" || (printf "Usage: make revision MSG='message'\n" && exit 1)
	$(COMPOSE) run --rm api uv run alembic revision --autogenerate -m "$(MSG)"

.PHONY: test
test:
	$(COMPOSE) run --rm api uv run pytest

.PHONY: test-local
test-local:
	cd $(BACKEND_DIR) && uv run pytest

.PHONY: shell
shell:
	$(COMPOSE) run --rm api bash
