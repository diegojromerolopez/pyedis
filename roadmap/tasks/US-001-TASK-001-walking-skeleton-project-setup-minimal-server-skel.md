# Task: Walking Skeleton, Project Setup & Minimal Server Skeleton

- **ID**: `US-001-TASK-001`
- **Story ID**: `US-001`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `[]` 
- **Target Files**: `pyproject.toml`, `requirements.txt`, `Makefile`, `README.md`, `.gitignore`, `src/__init__.py`, `src/main.py`, `tests/unit/__init__.py`, `tests/unit/test_server_skeleton.py`

## Description

Create project configuration (`pyproject.toml`, `requirements.txt`, `Makefile`, `README.md`, `.gitignore`), base package files (`src/__init__.py`, `tests/unit/__init__.py`), and `data/` directory. Implement a thin primary entrypoint in `src/main.py` (< 15 lines) calling a testable server factory `run_server(host, port, store, dispatcher)` listening on `127.0.0.1:${PORT:-6379}` over TCP with stdout/stderr prefixed with `pyedis: `. Implement a minimal handler returning `+PONG\r\n` on receiving basic `PING\r\n`. Co-locate basic unit/smoke tests in `tests/unit/test_server_skeleton.py` using standard `unittest.IsolatedAsyncioTestCase` verifying that `PING` receives `+PONG\r\n` within 30 seconds. Ensure `Makefile` has a `test` target executing `python3 -m unittest discover -s tests -v`. Strictly avoid pytest.
