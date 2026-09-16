# Task: Harden atomic protocol and expiration conformance

- **ID**: `US-003-TASK-003`
- **Story ID**: `US-003`
- **Status**: `PENDING`
- **Change Type**: `FIX`
- **Depends On**: `US-003-TASK-002`
- **Target Files**: `src/store.py`, `src/commands.py`, `src/server.py`, `tests/unit/test_store.py`, `tests/integration/test_server.py`

## Description

Run the complete executable contract matrix against the integrated implementation and correct any remaining store, command, or server behavior mismatches. Add or refine implementation where needed for exact envelopes and formatting across every command, including duplicate DEL/EXISTS keys, empty store, missing keys, boundary signed-64-bit integers, overflow and non-integer failures, NX/XX conflicts, EX/PX boundary validation, deadline equality, immediate expiration, persistent keys, glob escaping, deterministic key ordering, and concurrent pipelined increments. Verify that all time-based assertions use the injected fake clock at unit level and that integration tests do not depend on sleeps or wall-clock timing. Keep the server entrypoint thin and runnable, confirm all operations share the same async lock, and ensure expired keys are removed during downtime simulation and before scans/flushes. Execute python3 -m unittest discover -s tests -v and the documented black-box command scenario; use a minimal containerized runner for any unavailable external client tooling and do not mask failures or add tautological assertions.
