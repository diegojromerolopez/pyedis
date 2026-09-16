# Task: Build asyncio PING walking skeleton

- **ID**: `US-002-TASK-001`
- **Story ID**: `US-002`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `[]` 
- **Target Files**: `src/__init__.py`, `src/main.py`, `src/server.py`, `tests/integration/test_server.py`

## Description

Create the runnable server vertical slice. Implement a testable annotated server function in src/server.py (or an equivalent internal module) using only the Python standard library asyncio APIs. It must listen on PORT, defaulting to 6379, accept TCP clients, parse enough RESP2 arrays and inline commands to recognize PING case-insensitively, and return exactly b"+PONG\\r\\n". Keep src/main.py as a thin wrapper under 15 lines that delegates immediately to the testable server entrypoint, and add src/__init__.py. Add tests/integration/test_server.py as a Chicago-school black-box unittest that launches the real executable boundary, polls socket readiness without fixed sleeps, sends both a RESP PING and inline PING, and asserts exact response bytes and clean teardown. Ensure all functions have Python 3.10+ annotations, startup can be terminated by the test, and no pass, ellipsis, placeholder response, pytest artifact, or third-party dependency is introduced.
