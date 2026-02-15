.DEFAULT_GOAL := help

# ─── Environment ──────────────────────────────────────────────────────────────

.PHONY: install
install: ## Install all dependencies
	uv sync

.PHONY: lock
lock: ## Re-generate the uv lockfile
	uv lock

# ─── Run ──────────────────────────────────────────────────────────────────────

.PHONY: run
run: ## Start the Streamlit app
	uv run streamlit run app.py

.PHONY: run-dev
run-dev: ## Start the Streamlit app with auto-reload and debug logging
	uv run streamlit run app.py --server.runOnSave true --logger.level debug

# ─── Code Quality ─────────────────────────────────────────────────────────────

.PHONY: lint
lint: ## Run ruff linter
	uv run --with ruff ruff check .

.PHONY: lint-fix
lint-fix: ## Run ruff linter with auto-fix
	uv run --with ruff ruff check . --fix

.PHONY: format
format: ## Format code with ruff
	uv run --with ruff ruff format .

.PHONY: format-check
format-check: ## Check formatting without modifying files
	uv run --with ruff ruff format . --check

.PHONY: typecheck
typecheck: ## Run mypy type checking
	uv run --with mypy mypy app.py views/ src/

.PHONY: check
check: lint format-check ## Run all code quality checks (lint + format)

# ─── Build & Package ─────────────────────────────────────────────────────────

.PHONY: bump
bump: ## Bump version using commitizen (conventional commits)
	uv run --extra dev cz bump

.PHONY: release
release: ## Push commits and tags to remote
	git push && git push --tags

.PHONY: build
build: ## Build the distribution package
	uv build

# ─── Cleanup ──────────────────────────────────────────────────────────────────

.PHONY: clean
clean: ## Remove build artifacts and caches
	rm -rf dist/ build/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true

# ─── Help ─────────────────────────────────────────────────────────────────────

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
