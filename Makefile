# KubeSage development commands

VENV := .venv
PYTHON := $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python3)

.PHONY: help install test lint format typecheck security quality docker-build docker-run ci

help:
	@echo "[KubeSage] Available commands:"
	@echo "  make install     	Install project dependencies"
	@echo "  make format      	Format code with Ruff"
	@echo "  make lint        	Run Ruff linting"
	@echo "  make typecheck   	Run MyPy type checking"
	@echo "  make test        	Run test suite"
	@echo "  make security    	Run security audit"
	@echo "  make quality     	Run quality check"
	@echo "  make docker-build	Build the Docker image"
	@echo "  make docker-run  	Run the Docker image"
	@echo "  make ci          	Run CI checks"

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

quality: format lint typecheck test

# Security
security:
	$(PYTHON) -m pip_audit

# Docker 
docker-build:
	docker buildx build --platform linux/amd64 -t kubesage:dev .

docker-run:
	docker run -p 8000:8000 kubesage:dev

# Continuous Integration
ci: lint typecheck test security docker-build

# Clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache