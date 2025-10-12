.PHONY: help install install-dev test test-cov lint format type-check clean run init

help:
	@echo "ROM Groomer Python - Development Commands"
	@echo ""
	@echo "  make install          Install package"
	@echo "  make install-dev      Install package with dev dependencies"
	@echo "  make test             Run tests"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make lint             Lint code with ruff"
	@echo "  make format           Format code with black"
	@echo "  make type-check       Type check with mypy"
	@echo "  make clean            Clean build artifacts"
	@echo "  make init             Initialize ROM Groomer configuration"
	@echo "  make run              Run ROM Groomer CLI"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest -v

test-cov:
	pytest --cov --cov-report=term-missing --cov-report=html

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

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

init:
	romgroomer init

run:
	romgroomer --help

all: format lint type-check test
