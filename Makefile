SHORT_SHA := $(shell git rev-parse --short HEAD)
IMAGE_NAME := kubesage:$(SHORT_SHA)

.PHONY: help install test lint format typecheck security quality docker-build docker-run ci helm-lint helm-template kubeconform package db-upgrade db-revision db-current db-history db-downgrade bandit pip_audit trivy clean

help:
	@echo "[KubeSage] Available commands:"
	@echo "  make install     		Install project dependencies"
	@echo "  make format      		Format code with Ruff"
	@echo "  make lint        		Run Ruff linting"
	@echo "  make typecheck   		Run MyPy type checking"
	@echo "  make test        		Run test suite"
	@echo "  make bandit       		Run bandit static code analysis"
	@echo "  make pip_audit   		Run pip audit"
	@echo "  make trivy       		Run trivy vulnerability scan"
	@echo "  make docker-build		Build the Docker image"
	@echo "  make docker-run  		Run the Docker image"
	@echo "  make quality     		Run quality checks"
	@echo "  make security    		Run security audit"
	@echo "  make ci          		Run CI checks"
	@echo "  make helm-lint   		Run helm lint"
	@echo "  make helm-template 	Run helm template"
	@echo "  make kubeconform 		Run kubeconform"
	@echo "  make package 			Run helm package"
	@echo "  make db-upgrade 		Upgrade database schema"
	@echo "  make db-revision 		Create new migration"
	@echo "  make db-current 		Show current migration"
	@echo "  make db-history 		Show migration history"
	@echo "  make db-downgrade 		Downgrade database schema"

# Install dependencies

install:
	uv sync

# Testing

test:
	uv run pytest

# Code quality

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy .

quality: format lint typecheck test

# Security

bandit:
	@echo "Running bandit static code analysis..."
		uv run bandit -c pyproject.toml -r kubesage

pip_audit:
	@echo "Running pip audit..."
		uv run pip-audit

trivy:
	@echo "Running Trivy vulnerability scan..."
		trivy image $(IMAGE_NAME) --config trivy.yaml

security: bandit pip_audit trivy

# Helm

helm-lint:
	helm lint charts/kubesage

helm-template:
	helm template charts/kubesage

kubeconform:
	helm template charts/kubesage | kubeconform -summary -strict

package: helm-lint helm-template kubeconform

# Docker

docker-build:
	@echo "Building docker image..."
	docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t kubesage:${IMAGE_NAME} .

docker-run:
	@echo "Running docker image $(IMAGE_NAME) on port 8000..."
	docker run -p 8000:8000 $(IMAGE_NAME)

# Continuous Integration

ci: quality security docker-build

# Database

db-upgrade:
	uv run alembic upgrade head

db-revision:
	uv run alembic revision --autogenerate -m "$(MSG)"

db-current:
	uv run alembic current

db-history:
	uv run alembic history

db-downgrade:
	uv run alembic downgrade -1

# Clean

clean: |
	find . -type d -name "**pycache**" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
