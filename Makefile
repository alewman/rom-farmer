.PHONY: help install install-dev test test-cov lint format type-check clean clean-all run init build wizard

# =============================================================================
# ROM Groomer Python - Development Commands
# =============================================================================

help:
	@echo "ROM Groomer Python - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install package in editable mode"
	@echo "  make install-dev      Install package with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test             Run tests"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make lint             Lint code with ruff"
	@echo "  make lint-fix         Lint and auto-fix code"
	@echo "  make format           Format code with black"
	@echo "  make format-check     Check code formatting"
	@echo "  make type-check       Type check with mypy"
	@echo "  make all              Run format, lint, type-check, and test"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Clean Python build artifacts"
	@echo "  make clean-logs       Clean log and report files"
	@echo "  make clean-state      Clean build state files"
	@echo "  make clean-all        Clean everything (artifacts + logs + state)"
	@echo ""
	@echo "Running:"
	@echo "  make run              Show CLI help"
	@echo "  make wizard           Run interactive build wizard"
	@echo "  make build NAME=xxx   Run build 'xxx' (e.g., make build NAME=saturn-test)"
	@echo ""
	@echo "Project:"
	@echo "  make init             Initialize ROM Groomer configuration"
	@echo "  make ensure-dirs      Create required directories"

# =============================================================================
# Setup
# =============================================================================

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# =============================================================================
# Development
# =============================================================================

test:
	pytest -v tests/

test-cov:
	pytest --cov=src/romfarmer --cov-report=term-missing --cov-report=html tests/

lint:
	ruff check src/ tests/

lint-fix:
	ruff check --fix src/ tests/

format:
	black src/ tests/

format-check:
	black --check src/ tests/

type-check:
	mypy src/

all: format lint type-check test

# =============================================================================
# Cleanup
# =============================================================================

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .coverage htmlcov coverage.xml
	rm -rf .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-logs:
	rm -rf logs/*
	@echo "Cleaned logs/ directory"

clean-state:
	rm -rf state/*
	rm -f .build_state_*.yaml
	@echo "Cleaned state/ directory and state files"

clean-all: clean clean-logs clean-state
	rm -rf temp/
	@echo "Cleaned all artifacts, logs, state, and temp files"

# =============================================================================
# Running
# =============================================================================

init:
	romfarmer init

run:
	romfarmer --help

wizard:
	./build-wizard

# Build target - requires NAME parameter
build:
ifndef NAME
	$(error NAME is required. Usage: make build NAME=saturn-test)
endif
	romfarmer build run $(NAME)

# =============================================================================
# Project Setup
# =============================================================================

ensure-dirs:
	@mkdir -p logs state scripts/utilities docs/guides examples/configs temp metadata/database
	@echo "Created required directories"
