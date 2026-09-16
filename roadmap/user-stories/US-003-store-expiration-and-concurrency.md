# US-003 — In-Memory Store, Expiration Semantics & Atomic Concurrency

**depends_on:** ["US-001"]  
**change_type:** new

## User story
As a Redis client, I want atomic key operations and deterministic expiration behavior so that values, counters, TTLs, patterns, and concurrent requests behave like Redis.

## Requirements and atomic tasks

1. Implement `src/store.py` with an injected clock, in-memory values and expiration state, lazy eviction, active sweeps, async locking, and atomic compound operations; co-locate deterministic tests in `tests/unit/test_store.py`.
2. Integrate the real store with `src/commands.py` and the TCP server, adding redis-py integration tests for command behavior, pipelining, and concurrent clients in `tests/integration/test_server.py`.

## Definition of Done (DoD)

- GET, SET, DEL, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS, and FLUSHALL operate on real store state and return the exact envelopes specified in the refined specification.
- SET supports positive EX/PX, NX/XX, rejects duplicate/unknown/conflicting options, removes old TTLs on persistent overwrite, and preserves no state when a condition fails.
- INCR/DECR initialize missing keys, reject non-integers and signed 64-bit overflow, and preserve existing expiration. EXPIRE handles positive, zero, and negative values exactly. TTL returns -2, -1, or the correct positive floored remaining seconds without race-prone zero results.
- Lazy eviction occurs on every listed key access; KEYS and FLUSHALL sweep all expired keys first. KEYS supports `*`, `?`, `[abc]`, escaped literal `\\*`, and deterministic lexicographic output.
- All store operations, including reads and compound updates, are serialized by the shared async lock. Concurrent integration clients cannot lose increments or observe partially applied mutations.
- Every time-based unit test injects a fake clock and explicitly tests deadline equality, sub-second remaining time, expiration during downtime simulation, persistent keys, and immediate deletion. No wall-clock sleeps are used for deterministic assertions.
- Dedicated executable black-box scenarios exist for every command and capability in this story, including duplicate DEL/EXISTS keys, empty store, missing keys, boundary integers, NX/XX conflicts, EX/PX boundaries, glob patterns, and concurrent increments. Tests assert payloads and exact formatting.
- Tests use real domain objects and in-memory doubles at external boundaries. No pytest, live external database, or background broker is permitted. No stubs, masked failures, or tautological assertions are allowed. All unittest tests pass with exit code `0`; intermediate linting is advisory.

```noctifab-contract
{"story_id": "US-003","public_contracts":[{"id":"store.expiration-commands","interface":"TCP Redis-compatible command API","applicable_path_prefixes":["src/store.py","src/commands.py","tests/unit/","tests/integration/"],"allowed_executables":["python3 -m src.main","python3 -m unittest discover -s tests -v"],"exit_codes":[0],"stdout_contains":[],"stderr_prefixes":["pyedis: "]}]}
```