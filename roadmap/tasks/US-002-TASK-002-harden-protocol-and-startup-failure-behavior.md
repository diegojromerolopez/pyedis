# Task: Harden protocol and startup failure behavior

- **ID**: `US-002-TASK-002`
- **Story ID**: `US-002`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-002-TASK-001`
- **Target Files**: `src/server.py`, `src/main.py`, `tests/integration/test_server.py`

## Description

Extend the walking skeleton into a complete observable PING contract and co-located executable tests. Preserve the existing testable server interface while supporting mixed-case PING, fragmented request bytes, a pipelined pair of requests with two exact PONG replies, orderly connection close, and malformed or unsupported input without hanging. Validate PORT configuration before binding, report every malformed startup configuration and bind failure as stderr text beginning exactly with "pyedis: ", and exit with status 1; successful execution must remain compatible with python3 -m src.main and make run. Expand tests/integration/test_server.py with black-box subprocess scenarios that assert response bytes, stderr, and exit behavior, using readiness polling and dynamically selected ports where appropriate. Use injected or fake streams only for any lower-level parser tests added alongside the implementation; do not use fixed sleeps, pytest, external frameworks, or tautological assertions.
