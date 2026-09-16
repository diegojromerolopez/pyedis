# Task: Build thin TCP PING walking skeleton

- **ID**: `US-001-TASK-001`
- **Story ID**: `US-001`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `[]` 
- **Target Files**: `src/__init__.py`, `src/main.py`, `src/server.py`, `tests/integration/test_server.py`, `pyproject.toml`, `requirements.txt`

## Description

Create the minimal runnable Python package and server vertical slice. Add src/__init__.py and a testable internal server module or equivalent implementation boundary, plus src/main.py as a thin executable shell of fewer than 15 lines that immediately delegates to the server run/factory function. Implement an asyncio TCP server bound to 127.0.0.1 and the configured port boundary, accepting both RESP array PING (exactly *1\\r\\n$4\\r\\nPING\\r\\n) and inline PING\\r\\n, returning exactly +PONG\\r\\n. Make the server start/stop controllable in-process so tests do not need sleeps. Create tests/integration/test_server.py using only unittest.IsolatedAsyncioTestCase and a real loopback socket, including readiness polling and exact response assertions. Add initial pyproject.toml and requirements.txt with no third-party test framework or runtime dependency. Keep this slice runnable as python3 -m src.main with a sensible temporary/default port boundary, and ensure all assertions exercise the implementation rather than mocks that bypass networking.
