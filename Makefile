.PHONY: install build run test lint format e2e
install:
	python3 -m pip install -e ".[dev]"
build:
	python3 -m compileall src
	python3 -c 'import src.main'
run:
	python3 -m src.main
test:
	python3 -m unittest discover -s tests -v
lint:
	ruff check src tests
	mypy --strict src
format:
	ruff format src tests
e2e:
	@if command -v docker >/dev/null 2>&1; then docker compose -f docker-compose.e2e.yml up --build --exit-code-from e2e; else python3 -m unittest discover -s tests -v; fi
