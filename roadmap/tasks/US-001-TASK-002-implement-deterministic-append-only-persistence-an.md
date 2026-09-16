# Task: Implement deterministic append-only persistence and replay

- **ID**: `US-001-TASK-002`
- **Story ID**: `US-001`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`
- **Target Files**: `src/persistence.py`, `src/store.py`, `tests/unit/test_persistence.py`

## Description

Implement src/persistence.py as a testable persistence component supporting JSON-lines append records, configurable fsync, injected clock/logger/file seams, startup data-directory creation, ordered replay, absolute expire_at timestamps, expired-record eviction, corrupt trailing-line tolerance with exactly the diagnostic 'pyedis: ignoring corrupt trailing AOF line', failure on non-trailing corruption with a 'pyedis: ' diagnostic, and FLUSHALL truncation. Define clear record and persistence APIs usable by the command layer without embedding network concerns. Ensure append and fsync ordering can be observed, fsync=false skips os.fsync while preserving writes, file boundaries and partial final lines are testable, and replay never converts absolute timestamps to relative TTLs. Add co-located unittest coverage in tests/unit/test_persistence.py using temporary directories, fake clocks, in-memory stores, injected seams, restart round trips, expiration during downtime, valid-prefix/corrupt-tail cases, non-trailing corruption, and truncation. Use only the standard library and unittest.
