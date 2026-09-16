# Task: Implement AOF persistence engine and unit coverage

- **ID**: `US-004-TASK-001`
- **Story ID**: `US-004`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`
- **Target Files**: `src/persistence.py`, `tests/unit/test_persistence.py`

## Description

Create src/persistence.py as a testable persistence component for JSON-lines append-only logging and replay. Define the operation schema for SET, DEL, INCR, DECR, EXPIRE, and FLUSHALL; store SET and EXPIRE expirations as absolute timestamps; support configurable fsync after successful records; replay records sequentially against an injected clock; discard expired state without renewing relative TTLs; truncate the AOF for FLUSHALL; and recover only a corrupt or truncated final line while raising a prefixed fatal error for corrupt non-final lines. Ensure successful mutations append exactly one record and no-op conditional SET, missing DEL, and missing EXPIRE append none. Add co-located standard-library unittest coverage in tests/unit/test_persistence.py using TemporaryDirectory, fake clocks, malformed lines, restart-style replay, fsync spies, and byte-level truncation assertions. Keep the implementation independent of sockets and preserve the existing application entrypoint contract from US-001.
