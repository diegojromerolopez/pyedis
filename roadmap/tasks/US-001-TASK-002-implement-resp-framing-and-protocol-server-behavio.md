# Task: Implement RESP framing and protocol server behavior

- **ID**: `US-001-TASK-002`
- **Story ID**: `US-001`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`
- **Target Files**: `src/resp.py`, `src/main.py`, `tests/unit/test_resp.py`, `tests/integration/test_server.py`

## Description

Build src/resp.py as the framing boundary with concrete RESP2 array parsing, inline command parsing, CRLF-accurate encoding, fragmented TCP buffering support, empty-request handling, and deterministic malformed-input errors. Refactor the server core used by src/main.py so it recognizes command names case-insensitively and returns `+PONG\r\n` for both inline and array PING while keeping the entrypoint thin. Expand tests/unit/test_resp.py and tests/integration/test_server.py with Chicago-school unittest coverage for complete RESP request/reply exchange, fragmented input, inline versus array PING, lowercase and mixed-case names, empty requests, malformed input, no stdout diagnostics, clean startup, readiness polling, port-binding failure with `pyedis: ` stderr and exit 1, and orderly SIGINT/SIGTERM shutdown with exit 0. Ensure socket resources, event loops, child processes, and signal handlers are cleaned up deterministically and that all protocol writes use CRLF exactly.
