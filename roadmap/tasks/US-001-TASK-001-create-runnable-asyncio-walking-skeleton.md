# Task: Create runnable asyncio walking skeleton

- **ID**: `US-001-TASK-001`
- **Story ID**: `US-001`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `[]` 
- **Target Files**: `pyproject.toml`, `requirements.txt`, `Makefile`, `.gitignore`, `src/__init__.py`, `src/main.py`, `tests/integration/test_server.py`

## Description

Create the initial runnable project shell and a thin src/main.py wrapper under 15 lines that immediately delegates to a testable server entrypoint. Add pyproject.toml, requirements.txt with no third-party runtime dependencies, Makefile whose run target invokes the supported module and whose test target is exactly `python3 -m unittest discover -s tests -v`, .gitignore, src/__init__.py, and the initial tests/integration/test_server.py. Implement a minimal asyncio TCP listener bound to 127.0.0.1 and PORT (default 6379), with a concrete request handler sufficient to accept inline PING and return the exact `+PONG\r\n` payload. Expose a clean startup/readiness mechanism for tests, avoid stdout diagnostics, report fatal startup errors to stderr with the `pyedis: ` prefix and exit code 1, and support orderly shutdown with exit code 0. The co-located unittest must launch the process or testable entrypoint, poll socket readiness rather than sleep, physically send PING, assert the exact response, and terminate deterministically in under 30 seconds. Do not add persistence or a broad command hierarchy here.
