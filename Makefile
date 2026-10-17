.PHONY: all build test lint format e2e clean run

all: build

build:
	uv venv --seed --clear .venv
	uv pip install -e ".[dev]"

install:
	uv venv --seed --clear .venv
	uv pip install -e ".[dev]"

run:
	uv run python -m src.main

test:
	python3 -m unittest discover -s tests -v

lint:
	uv run ruff check src tests
	uv run mypy --strict src

format:
	uv run ruff format src tests

e2e:
	docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from test-runner-e2e

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .venv .mypy_cache .ruff_cache htmlcov .coverage data/
