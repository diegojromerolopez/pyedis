# Task: Implement atomic expiring in-memory store

- **ID**: `US-003-TASK-001`
- **Story ID**: `US-003`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`
- **Target Files**: `src/store.py`, `tests/unit/test_store.py`

## Description

Create or complete src/store.py as the real domain store used by the application. Inject a clock abstraction that supports deterministic fake-clock tests, maintain value and expiration state, and serialize every operation, including reads, with one shared asyncio lock. Implement GET, SET, DEL, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS, and FLUSHALL with lazy eviction on every listed key access and full expiration sweeps before KEYS and FLUSHALL. Implement SET option parsing and validation for positive EX/PX, NX/XX, duplicate options, unknown options, and conflicting options; failed conditions must not mutate value or TTL, while successful persistent overwrites remove old expiration. Implement signed 64-bit validation, missing-key initialization, preservation of expiration during INCR/DECR, exact EXPIRE zero/negative deletion semantics, TTL -2/-1/positive floored values without race-prone zero results, and deterministic glob matching for *, ?, [abc], and escaped literal \\*. Return domain results/envelopes compatible with the existing command layer and refined contract. Add co-located unittest coverage in tests/unit/test_store.py using real store objects and a fake clock for deadline equality, sub-second remaining time, downtime expiration simulation, persistent keys, immediate deletion, missing keys, duplicate keys, boundary integers, option failures, glob patterns, lexicographic ordering, and concurrent atomic updates. Do not use pytest, wall-clock sleeps, external services, or tautological assertions.
