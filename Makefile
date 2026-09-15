install:
	python3 -m pip install -e ".[dev]"

build:
	python3 -m compileall src
	python3 -c 'import src.main'

test:
	python3 -m unittest discover -s tests -v

lint:
	ruff check src tests
	mypy --strict src

format:
	ruff format src tests

run:
	python3 -m src.main

e2e:
	python3 -m unittest discover -s tests -v
