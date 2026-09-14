# Task: Implement AOF Persistence Engine with Absolute Timestamp Logging and Fault-Tolerant Replay

- **ID**: `US-003-TASK-001`
- **Story ID**: `US-003`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`
- **Target Files**: `src/persistence.py`, `tests/unit/test_persistence.py`

## Description

Implement `AOFEngine` in `src/persistence.py` to persist state mutations as single JSON lines in `<PYEDIS_DATA_DIR>/dump.aof` with absolute epoch timestamp (`expire_at`). Implement optional `os.fsync()` execution when environment variable `PYEDIS_AOF_FSYNC=true`. Build sequential startup replay into `Store`, incorporating corrupt trailing line recovery that logs `pyedis: ignoring corrupt trailing AOF line` while restoring valid prior state. Provide `flushall()` truncation to zero bytes. Add co-located unit tests in `tests/unit/test_persistence.py` testing replay recovery, fsync handling, and expiration retention.
