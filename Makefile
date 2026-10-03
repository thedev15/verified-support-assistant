SHELL := /bin/bash
PYTHON ?= python
HOST ?= 127.0.0.1
PORT ?= 8000

.DEFAULT_GOAL := help
.PHONY: help setup install install-sandbox frontend-install frontend-check frontend-build browser lint format format-check test evaluate check run run-public docker-build docker-run capture clean

help: ## Show the available development commands
	@awk 'BEGIN {FS = ":.*## "; printf "Verified Support Assistant commands:\n\n"} /^[a-zA-Z_-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: install ## Install development dependencies

install: ## Install the app and development tools in editable mode
	$(PYTHON) -m pip install -e ".[dev]"

install-sandbox: ## Install optional CoreWeave Sandbox tooling
	$(PYTHON) -m pip install -e ".[dev,sandbox]"

frontend-install: ## Install locked frontend dependencies
	npm --prefix web ci

frontend-check: ## Generate API types, typecheck, and run component tests
	npm --prefix web run check

frontend-build: ## Build hashed React assets for FastAPI
	npm --prefix web run build

browser: ## Install Chromium for local screenshot capture
	$(PYTHON) -m playwright install chromium

lint: ## Run static analysis
	$(PYTHON) -m ruff check .

format: ## Format Python files
	$(PYTHON) -m ruff format .

format-check: ## Verify Python formatting without changing files
	$(PYTHON) -m ruff format --check .

test: ## Run the unit and API test suite
	$(PYTHON) -m pytest -q

evaluate: ## Run the deterministic 40-case evaluation
	$(PYTHON) -m support_assistant.evaluate

check: lint format-check test evaluate frontend-check frontend-build ## Run every quality gate

run: ## Start the local development server on 127.0.0.1:8000
	$(PYTHON) -m uvicorn support_assistant.api:app --reload --host $(HOST) --port $(PORT)

run-public: ## Start on all interfaces (only on a trusted network)
	$(PYTHON) -m uvicorn support_assistant.api:app --host 0.0.0.0 --port $(PORT)

docker-build: ## Build the production-style container image
	docker build -t verified-support-assistant:local .

docker-run: ## Run the container at http://localhost:8000
	docker run --rm -p 8000:8000 verified-support-assistant:local

capture: ## Capture all 40 UI evidence cases from a running local server
	$(PYTHON) scripts/capture_live_demo.py --base-url http://127.0.0.1:$(PORT)

clean: ## Remove generated Python and test caches
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache \) -prune -exec rm -rf {} +