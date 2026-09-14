build:
	python3 -m compileall -q src
install:
	python3 -m pip install -e ".[dev]"
run:
	python3 -m src.main
test:
	python3 -m unittest discover -s tests -v
lint:
	ruff check src tests
	mypy --strict src
format:
	ruff format src tests
e2e: build
	python3 -m unittest discover -s tests -v
