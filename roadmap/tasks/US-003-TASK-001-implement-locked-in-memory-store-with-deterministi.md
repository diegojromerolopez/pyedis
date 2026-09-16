# Task: Implement locked in-memory store with deterministic expiration

- **ID**: `US-003-TASK-001`
- **Story ID**: `US-003`
- **Status**: `PENDING`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`
- **Target Files**: `src/store.py`, `tests/unit/test_store.py`

## Description

Create src/store.py as the real in-memory domain store, using the interfaces and entrypoint conventions supplied by US-001-TASK-001. Define an injectable clock abstraction or callable, value and deadline state, and one shared asyncio lock used by every read, write, scan, expiration, and compound operation. Implement atomic GET, SET, DEL, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS, and FLUSHALL behavior. Include lazy eviction on every applicable key access and full expired-key sweeps before KEYS and FLUSHALL. Implement SET option parsing and validation for positive EX/PX, NX/XX, duplicate/unknown/conflicting options, persistent overwrite TTL removal, and no mutation on failed conditions. Implement signed 64-bit integer parsing and overflow checks, missing-key initialization, preservation of expiration during INCR/DECR, EXPIRE zero/negative deletion, and TTL values -2, -1, or correctly floored positive seconds without race-prone zero results. Implement Redis-style glob matching for *, ?, [abc], and escaped literal \\*, with lexicographically sorted keys. Add co-located unittest coverage in tests/unit/test_store.py using a fake clock for deadline equality, sub-second remaining time, downtime expiration simulation, persistent keys, immediate deletion, missing and duplicate keys, boundaries, and serialized concurrent compound operations. Do not use wall-clock sleeps, pytest, or external databases.
