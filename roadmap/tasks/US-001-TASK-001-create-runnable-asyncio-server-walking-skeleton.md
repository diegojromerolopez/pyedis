# Task: Create runnable asyncio server walking skeleton

- **ID**: `US-001-TASK-001`
- **Story ID**: `US-001`
- **Status**: `PENDING`
- **Change Type**: `FEATURE`
- **Depends On**: `[]` 
- **Target Files**: `src/__init__.py`, `src/main.py`, `tests/integration/test_server.py`

## Description

Create src/__init__.py and a thin src/main.py entrypoint whose module execution delegates immediately to a testable core run/start function. Implement the minimal asyncio TCP listener boundary on 127.0.0.1 using PORT from the environment, with an injectable or directly callable server lifecycle suitable for unittest.IsolatedAsyncioTestCase. Provide a minimal connection handler that can accept and close connections cleanly, startup failure reporting with the `pyedis: ` stderr prefix and exit status 1, and clean SIGINT/SIGTERM shutdown with status 0. Add tests/integration/test_server.py containing a real-socket smoke test that starts the server through the testable boundary, verifies readiness and clean teardown, and confirms the primary module can remain a thin shell. Use unittest only, no pytest, no third-party runtime dependencies, and no prohibited placeholders such as pass or ellipsis. Keep this slice runnable independently before protocol behavior is added.
