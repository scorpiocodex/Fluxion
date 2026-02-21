# ──────────────────────────────────────────────────
# FLUXION — Makefile
# ──────────────────────────────────────────────────

.PHONY: help install dev lint format typecheck test coverage build clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install Fluxion
	pip install -e .

dev: ## Install with dev dependencies
	pip install -e ".[dev]"
	pre-commit install

lint: ## Run linter
	ruff check fluxion/ tests/

format: ## Format code
	black fluxion/ tests/

typecheck: ## Run type checker
	mypy fluxion/ --ignore-missing-imports

test: ## Run tests
	pytest -q

coverage: ## Run tests with coverage report
	pytest --cov=fluxion --cov-report=term-missing --cov-report=html

build: ## Build distribution packages
	python -m build

clean: ## Remove build artifacts
	rm -rf dist/ build/ *.egg-info htmlcov/ .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
