# Task: Implement deterministic JSON-lines AOF persistence

- **ID**: `US-001-TASK-002`
- **Story ID**: `US-001`
- **Status**: `PENDING`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`
- **Target Files**: `src/persistence.py`, `src/store.py`, `src/commands.py`, `tests/unit/test_persistence.py`

## Description

Create src/persistence.py as a testable persistence component for PYEDIS_DATA_DIR/dump.aof. Implement configurable append and flush behavior, optional os.fsync controlled by PYEDIS_AOF_FSYNC, operation records for SET, DEL, INCR, DECR, positive EXPIRE, and immediately-expired non-positive EXPIRE, absolute expire_at timestamps, ordered replay into an injected/in-memory store, expiration eviction using an injected clock, startup directory creation, FLUSHALL truncation, and safe resource handling. Define clear seams for clock, file operations, fsync, and logging so tests do not depend on wall-clock timing or uncontrolled filesystem behavior. Ensure each successful mutation produces exactly one valid JSON line, failed conditionals/reads/missing-key operations produce none, replay never converts absolute timestamps to relative TTLs, a malformed or truncated final line logs exactly "pyedis: ignoring corrupt trailing AOF line" while preserving prior records, and non-trailing corruption raises a startup error suitable for exit code 1. Add tests/unit/test_persistence.py in the same task using unittest, temporary directories, fake clocks, injected file boundaries, in-memory stores, logger seams, restart round trips, expiration during downtime, fsync/flush ordering, and truncation assertions. Keep all tests deterministic and free of pytest or third-party frameworks.
