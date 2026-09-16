# Task: Establish thin server entrypoint and characterize existing command behavior

- **ID**: `US-001-TASK-001`
- **Story ID**: `US-001`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `[]` 
- **Target Files**: `src/main.py`, `src/server.py`, `tests/integration/test_server.py`, `tests/unit/test_main.py`

## Description

Create or preserve a minimal primary entrypoint in src/main.py that delegates immediately to a testable server/application function and remains under 15 lines at the shell boundary. Add or update unittest-based characterization coverage for the existing RESP2 server entrypoint, readiness behavior, successful and failed command responses, process exit behavior, and current data-directory configuration. Keep this slice runnable without persistence changes and ensure the server can be started by the documented python3 -m src.main contract. Do not introduce third-party test frameworks or host-installed dependencies. Tests must execute real in-process entrypoints or subprocesses as appropriate and must not be connect-only smoke tests.
