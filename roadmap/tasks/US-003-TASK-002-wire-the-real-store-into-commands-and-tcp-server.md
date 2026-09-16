# Task: Wire the real store into commands and TCP server

- **ID**: `US-003-TASK-002`
- **Story ID**: `US-003`
- **Status**: `PENDING`
- **Change Type**: `FEATURE`
- **Depends On**: `US-003-TASK-001`
- **Target Files**: `src/commands.py`, `src/server.py`, `src/main.py`, `tests/integration/test_server.py`

## Description

Integrate the completed store into src/commands.py and the TCP server without bypassing the shared async lock or maintaining duplicate state. Preserve the existing thin primary entrypoint and domain/envelope conventions from US-001, and ensure each supported command returns the exact refined Redis-compatible response payload and formatting. Add command parsing and dispatch for SET option combinations, counters, expiration, patterns, duplicate DEL/EXISTS arguments, empty and missing keys, and FLUSHALL. Ensure one shared store instance is used by all client connections and pipelined requests, and that malformed arguments produce the established protocol error envelope. Add redis-py integration tests in tests/integration/test_server.py that launch the real server through the project entrypoint, exercise every command and capability, verify pipelining and exact payloads, and run concurrent client increments to prove no lost updates or partially applied mutations. Use in-memory doubles only at external boundaries and unittest; if a Redis-compatible client dependency or runner is needed, execute it in a minimal containerized runner rather than requiring host installations.
