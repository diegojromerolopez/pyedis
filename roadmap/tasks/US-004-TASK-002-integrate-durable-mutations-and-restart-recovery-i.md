# Task: Integrate durable mutations and restart recovery into server

- **ID**: `US-004-TASK-002`
- **Story ID**: `US-004`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-004-TASK-001`
- **Target Files**: `src/main.py`, `src/server.py`, `src/commands.py`, `src/store.py`, `tests/integration/test_server.py`

## Description

Wire the persistence engine into the real server state and command dispatch paths in src/main.py and the relevant existing src modules. Persist every effective SET, DEL, INCR, DECR, EXPIRE, and FLUSHALL at the mutation boundary, preserve absolute expiration semantics across downtime, and make FLUSHALL clear memory and truncate data/dump.aof. When PYEDIS_AOF_FSYNC=true, perform fsync after the record is written and before the corresponding RESP reply is sent; when false, skip fsync but retain the record. Load and replay the AOF before accepting requests, inject or consistently use the server clock, and emit the exact trailing-corruption log message while prefixing fatal startup errors with pyedis:. Add or extend tests/integration/test_server.py with unittest-based restart tests for persistent values, counters, live and expired TTLs, SIGKILL-style trailing corruption, fsync ordering, no-op mutation behavior, and FLUSHALL truncation. Maintain a thin primary entrypoint that delegates to a testable server runner.
