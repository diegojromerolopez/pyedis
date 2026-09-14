# Task: Implement AOF Persistence & Startup Replay Engine

- **ID**: `US-002-TASK-002`
- **Story ID**: `US-002`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-002-TASK-001`
- **Target Files**: `src/persistence.py`, `src/store.py`, `src/commands.py`, `tests/unit/test_persistence.py`

## Description

Implement `src/persistence.py` with `AOFLogger`:
- Write state mutations as JSON lines (`{"op":"SET","key":"k","value":"v","expire_at":12345.6}`) to `${PYEDIS_DATA_DIR}/dump.aof`.
- Support `PYEDIS_AOF_FSYNC=true` setting by calling `os.fsync` on writes.
- Implement startup replay engine that reads `dump.aof`, evicts expired keys immediately upon replay based on clock timestamp without resetting TTL, and gracefully tolerates truncated/corrupt trailing lines by outputting `pyedis: ignoring corrupt trailing AOF line` to stderr without crashing.
- Support AOF truncation to zero bytes upon `FLUSHALL` command execution.

Co-locate unit tests in `tests/unit/test_persistence.py`.
