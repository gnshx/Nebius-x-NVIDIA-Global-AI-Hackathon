# =============================================================================
# RepoMedic Makefile
# =============================================================================

.PHONY: help setup dev down test test-unit test-integration test-e2e lint format \
        migrate migrate-create type-check demo clean logs shell-api shell-db

# Detect OS for open command
UNAME := $(shell uname)
ifeq ($(UNAME), Darwin)
    OPEN := open
else
    OPEN := xdg-open
endif

help: ## Show this help message
	@echo "RepoMedic — Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
setup: ## Install all dependencies and initialize the project
	@echo "→ Checking Docker..."
	@docker --version || (echo "ERROR: Docker not found. Install Docker first." && exit 1)
	@echo "→ Copying .env.example to .env (if not exists)..."
	@test -f .env || cp .env.example .env
	@echo "→ Building Docker images..."
	docker compose build
	@echo "→ Starting infrastructure (postgres, redis)..."
	docker compose up -d postgres redis
	@echo "→ Waiting for postgres to be ready..."
	@sleep 5
	@echo "→ Running database migrations..."
	docker compose run --rm api alembic upgrade head
	@echo ""
	@echo "✅ Setup complete! Run 'make dev' to start the full stack."

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------
dev: ## Start the full development stack
	docker compose up -d
	@echo ""
	@echo "✅ RepoMedic is running:"
	@echo "   API:      http://localhost:8000"
	@echo "   API docs: http://localhost:8000/docs"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Redis:    localhost:6379"
	@echo "   Postgres: localhost:5432"
	@echo ""
	@echo "Run 'make logs' to follow logs."

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

logs: ## Follow all service logs
	docker compose logs -f

logs-api: ## Follow API logs only
	docker compose logs -f api

logs-worker: ## Follow worker logs only
	docker compose logs -f worker

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
migrate: ## Run Alembic database migrations
	docker compose run --rm api alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create NAME="description")
	docker compose run --rm api alembic revision --autogenerate -m "$(NAME)"

migrate-down: ## Rollback last migration
	docker compose run --rm api alembic downgrade -1

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------
test: test-unit test-integration ## Run unit + integration tests

test-unit: ## Run unit tests
	docker compose run --rm api pytest tests/unit/ -v --tb=short

test-integration: ## Run integration tests
	docker compose run --rm api pytest tests/integration/ -v --tb=short --asyncio-mode=auto

test-e2e: ## Run end-to-end tests (requires running stack)
	docker compose run --rm api pytest tests/e2e/ -v --tb=short --asyncio-mode=auto

test-cov: ## Run tests with coverage report
	docker compose run --rm api pytest tests/unit/ tests/integration/ \
		--cov=. --cov-report=term-missing --cov-report=html:/tmp/coverage \
		-v --tb=short

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------
lint: ## Run ruff linter on backend
	docker compose run --rm api ruff check .
	@echo "→ Checking frontend..."
	docker compose run --rm web npm run lint

format: ## Format backend (black + ruff) and frontend (prettier)
	docker compose run --rm api black .
	docker compose run --rm api ruff check --fix .
	docker compose run --rm web npm run format

type-check: ## Run mypy (backend) and tsc (frontend)
	docker compose run --rm api mypy . --strict --ignore-missing-imports
	docker compose run --rm web npx tsc --noEmit

# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
demo-live: ## Run live 12-node autonomous agent demo in terminal
	@echo "→ Executing RepoMedic Live Agent..."
	python3 scripts/run_live_demo.py

demo: ## Seed demo repo and start a demo agent run
	@echo "→ Starting demo..."
	docker compose up -d
	@sleep 3
	docker compose run --rm api python scripts/seed_demo.py
	@echo ""
	@echo "✅ Demo run started! Opening dashboard..."
	@sleep 2
	$(OPEN) http://localhost:3000/runs 2>/dev/null || echo "Open http://localhost:3000/runs"

# ---------------------------------------------------------------------------
# Shells
# ---------------------------------------------------------------------------
shell-api: ## Open a shell in the API container
	docker compose exec api bash

shell-db: ## Open a psql shell
	docker compose exec postgres psql -U repomedic -d repomedic

shell-redis: ## Open a redis-cli shell
	docker compose exec redis redis-cli

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
clean: ## Remove containers, volumes, and build artifacts
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
