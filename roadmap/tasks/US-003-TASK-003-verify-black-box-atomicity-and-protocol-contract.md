# Task: Verify black-box atomicity and protocol contract

- **ID**: `US-003-TASK-003`
- **Story ID**: `US-003`
- **Status**: `SUCCESS`
- **Change Type**: `FIX`
- **Depends On**: `US-003-TASK-002`
- **Target Files**: `src/store.py`, `src/commands.py`, `src/server.py`, `src/main.py`, `tests/unit/test_store.py`, `tests/integration/test_server.py`

## Description

Run and complete the executable black-box contract matrix against the actual TCP entrypoint, then fix implementation defects found at the command/server boundary. Cover every command and capability in this story with exact payload assertions: empty store and missing keys, duplicate DEL/EXISTS arguments, signed 64-bit boundaries and overflow, non-integer counters, NX/XX success and no-op cases, EX/PX positive and invalid boundaries, TTL -2/-1/positive flooring, immediate expiration, persistent overwrites, escaped and character-class glob patterns, deterministic KEYS order, FLUSHALL expiration cleanup, pipelined ordering, and high-contention concurrent increments with no lost updates or partially applied mutations. Add only concrete compatibility or lifecycle fixes needed to keep the real store and server atomic and consistently formatted, with any new tests co-located in tests/integration/test_server.py or the affected implementation module. Verify the mandated unittest commands and exit code 0; do not mask failures, add sleeps, rely on pytest, or install host tools. Use a minimal containerized runner for any optional external executable needed by the verification.
