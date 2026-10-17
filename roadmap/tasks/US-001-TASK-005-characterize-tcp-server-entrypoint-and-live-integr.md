# Task: Characterize TCP server entrypoint and live integration

- **ID**: `US-001-TASK-005`
- **Story ID**: `US-001`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`, `US-001-TASK-002`, `US-001-TASK-003`, `US-001-TASK-004`
- **Target Files**: `src/main.py`, `tests/integration/__init__.py`, `tests/integration/test_server.py`, `tests/e2e/run_tests.sh`

## Description

Keep `src/main.py` as a thin wrapper below 15 lines. Write integration tests in `tests/integration/test_server.py` using `unittest.IsolatedAsyncioTestCase`. Verify live socket communication, readiness polling, and client disconnects. Maintain `tests/e2e/run_tests.sh` executable harness.
