VENV := .venv
PYTHON := $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python3,$(VENV)/bin/python,python)

.PHONY: install test lint format typecheck

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

typecheck:
	$(PYTHON) -m mypy .

check: lint typecheck test

fix:
	$(PYTHON) -m ruff check . --fix
	$(PYTHON) -m ruff format .