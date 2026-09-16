# Task: Implement command store and RESP dispatch surface

- **ID**: `US-002-TASK-003`
- **Story ID**: `US-002`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-002-TASK-001`, `US-002-TASK-002`
- **Target Files**: `src/commands.py`, `src/server.py`, `src/main.py`, `tests/unit/test_commands.py`, `tests/integration/test_server.py`

## Description

Implement src/commands.py as a testable command parser/dispatcher integrated with the RESP stream and server lifecycle. Provide an injected in-memory store double and deterministic fake clock interfaces for tests, without external databases or brokers. Implement case-insensitive PING, ECHO, QUIT, SET with exact option syntax and conditional behavior, GET, DEL, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS, FLUSHALL, unknown-command errors preserving the original unknown name, and optional discovery fallback if the existing architecture exposes one. Match refined Redis-compatible RESP2 replies and exact lowercase command names in arity errors, integer/syntax/conditional SET errors, null bulk values, arrays, and FIFO pipelined responses. Connect malformed protocol handling so safe protocol errors are emitted and the connection closes as required; support inline and binary-safe requests. Add co-located unit tests in tests/unit/test_commands.py and live integration scenarios in tests/integration/test_server.py, with one complete-envelope black-box scenario for every required command plus malformed protocol, pipelining, inline input, binary values, and deterministic time behavior. Verify python3 -m unittest discover -s tests -v exits zero, keep all source files under 500 lines, and ensure src/main.py remains a thin wrapper. If container execution is needed, use a minimal containerized Python runner rather than host installation.
