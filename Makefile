# KubeSage development commands

VENV := .venv
PYTHON := $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python3)

.PHONY: help install test lint format typecheck check fix dev-run dev-stop

help:
	@echo "Available commands:"
	@echo "  make install     Install project dependencies"
	@echo "  make test        Run test suite"
	@echo "  make lint        Run Ruff linting"
	@echo "  make format      Format code with Ruff"
	@echo "  make typecheck   Run MyPy type checking"
	@echo "  make check       Run lint + typecheck + tests"
	@echo "  make fix         Automatically fix lint and formatting issues"
	@echo "  make dev-start   Start local development environment"
	@echo "  make dev-stop    Stop local development environment"


# Install dependencies
install:
	$(PYTHON) -m pip install -e ".[dev]"


# Testing
test:
	$(PYTHON) -m pytest


# Code quality
lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

typecheck:
	$(PYTHON) -m mypy .


# Full validation pipeline
check: lint typecheck test


# Automatic code fixes
fix:
	$(PYTHON) -m ruff check . --fix
	$(PYTHON) -m ruff format .
