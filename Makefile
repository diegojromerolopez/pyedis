.PHONY: install run test lint format e2e clean

install:
	pip install -r requirements.txt || true

run:
	python3 -m src.main

test:
	python3 -m unittest discover -s tests -v

lint:
	ruff check src tests && mypy --strict src

format:
	ruff format src tests || ruff check --fix src tests

e2e:
	# NOTE: docker-compose (v1 standalone CLI) is deprecated and no longer supported.
	# The correct command is `docker compose` (Docker Compose v2 plugin).
	docker compose -f docker-compose.e2e.yml up --build --exit-code-from test-runner-e2e

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__ tests/unit/__pycache__ .mypy_cache .ruff_cache
