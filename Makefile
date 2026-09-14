.PHONY: all install run test lint format e2e

all: test

install:
	python3 -m pip install -e ".[dev]"

run:
	python3 -m src.main

test:
	python3 -m unittest discover -s tests -t . -v

lint:
	ruff check src tests
	mypy --strict src

format:
	ruff format src tests

e2e:
	docker compose up --build --exit-code-from e2e
