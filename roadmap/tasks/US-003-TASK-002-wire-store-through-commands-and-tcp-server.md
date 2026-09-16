# Task: Wire store through commands and TCP server

- **ID**: `US-003-TASK-002`
- **Story ID**: `US-003`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-003-TASK-001`
- **Target Files**: `src/commands.py`, `src/server.py`, `src/main.py`, `tests/integration/test_server.py`

## Description

Integrate the store from US-003-TASK-001 into src/commands.py and the TCP server without introducing per-request stores or bypassing the shared lock. Ensure GET, SET, DEL, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS, and FLUSHALL dispatch to real state and emit the exact Redis-compatible payloads and formatting already defined by the project contract, including errors for malformed, duplicate, unknown, conflicting, and out-of-range arguments. Preserve one store across clients and requests, support pipelined commands in order, and keep the primary entrypoint as a thin shell delegating to the testable server/core entrypoint. Add or update tests/integration/test_server.py using the real server and redis-py clients to exercise command behavior, option boundaries, duplicate DEL/EXISTS keys, empty and missing keys, persistence and expiration behavior, glob patterns, pipelining, and concurrent clients performing increments. Use deterministic in-memory doubles only where an external boundary requires one; do not add pytest, live Redis, background brokers, or wall-clock sleeps for deterministic assertions. If a runner needs external tooling, document/use a minimal containerized runner rather than host installation.
