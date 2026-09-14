.PHONY: build install run test lint format e2e

build:
	python3 -m compileall -q src

install:
	python3 -m pip install -e ".[dev]"

run:
	python3 -m src.main

test:
	@count=$$(python3 -m unittest discover -s tests -v 2>&1 | tee /dev/stderr | grep -E '^(Ran|FAILED|OK)' | tail -1); \
	case "$$count" in Ran\ 0\ tests*) echo 'No tests were discovered' >&2; exit 1;; esac

lint:
	ruff check src tests
	mypy --strict src

format:
	ruff format src tests

e2e:
	docker compose up --build --exit-code-from e2e
