# Task: Asyncio TCP Server Composition Root, Signal Handling, and Integration Tests

- **ID**: `US-004-TASK-001`
- **Story ID**: `US-004`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-002-TASK-001`, `US-003-TASK-001`
- **Target Files**: `src/main.py`, `tests/integration/test_server.py`

## Description

Implement the main entrypoint in `src/main.py` using `asyncio.start_server` bound to `0.0.0.0` and port specified by `PORT` env var (default `6379`). Structure as a thin entrypoint delegating to an async `run_server` function. Register `SIGINT` and `SIGTERM` signal handlers to gracefully shut down open client connections, flush pending AOF writes/open files, stop the server socket, and exit with status code 0. Log operational diagnostic messages prefixed with `pyedis: `. Add integration tests in `tests/integration/test_server.py` using `redis-py` to test server startup/shutdown, high concurrency (50 parallel client operations), command pipelining, and clean signal termination.
