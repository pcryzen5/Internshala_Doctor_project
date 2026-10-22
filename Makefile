.PHONY: help dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend install clean

ifeq ($(OS),Windows_NT)
    BACKEND_PYTHON := .venv/Scripts/python.exe
    ROOT_PYTHON := backend/.venv/Scripts/python.exe
    NPM := npm.cmd
else
    BACKEND_PYTHON := .venv/bin/python
    ROOT_PYTHON := backend/.venv/bin/python
    NPM := npm
endif

PYTHON_EXEC := $(wildcard $(ROOT_PYTHON))
ifeq ($(strip $(PYTHON_EXEC)),)
    PYTHON_EXEC := python
    BACKEND_PY := python
else
    BACKEND_PY := $(BACKEND_PYTHON)
endif

help:
	@echo "Available commands:"
	@echo "  make dev           - Run backend and frontend concurrently"
	@echo "  make test          - Run backend and frontend tests"
	@echo "  make lint          - Run ruff, mypy, oxlint, and tsc"
	@echo "  make install       - Install backend and frontend dependencies"
	@echo "  make clean         - Clean temporary build and cache files"

install:
	cd backend && $(BACKEND_PY) -m pip install -e ".[dev]"
	cd frontend && $(NPM) install

dev-backend:
	cd backend && $(BACKEND_PY) -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend:
	cd frontend && $(NPM) run dev

dev:
	$(PYTHON_EXEC) scripts/run_dev.py

test-backend:
	cd backend && $(BACKEND_PY) -m pytest tests -v

test-frontend:
	cd frontend && $(NPM) run test

test: test-backend test-frontend

lint-backend:
	cd backend && $(BACKEND_PY) -m ruff check app tests
	cd backend && $(BACKEND_PY) -m ruff format --check app tests
	cd backend && $(BACKEND_PY) -m mypy app

lint-frontend:
	cd frontend && $(NPM) run lint
	cd frontend && $(NPM) run typecheck

lint: lint-backend lint-frontend

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
