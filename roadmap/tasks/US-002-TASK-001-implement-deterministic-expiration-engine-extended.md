# Task: Implement Deterministic Expiration Engine & Extended Commands

- **ID**: `US-002-TASK-001`
- **Story ID**: `US-002`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`
- **Target Files**: `src/store.py`, `src/commands.py`, `tests/unit/test_store.py`, `tests/unit/test_commands.py`

## Description

Extend `src/store.py` with an expiration index using Unix epoch timestamps via an injected `Clock` (`Callable[[], float]`). Implement dual-mode eviction: lazy eviction upon key access, and active sweep before executing `KEYS` or `FLUSHALL`. Extend `src/commands.py` with support for commands and semantics:
- `SET key val [EX seconds] [PX milliseconds] [NX|XX]`: Handle TTL options, mutual exclusivity of NX/XX (returning `-ERR syntax error\r\n`), and clearing existing TTL on plain `SET` overwrite.
- `INCR key` and `DECR key`: Initialize missing keys to 0 before mutating; preserve existing TTL.
- `EXPIRE key seconds`: Delete immediately if `seconds <= 0`.
- `TTL key`: Return remaining integer seconds, `-1` for persistent key, `-2` for missing/expired key.
- `KEYS pattern`: Perform glob pattern matching (`*`, `?`, `[abc]`, `\*`) following active sweep.
- `FLUSHALL`: Purge all keys from store.

Co-locate unit tests in `tests/unit/test_store.py` and `tests/unit/test_commands.py`.
