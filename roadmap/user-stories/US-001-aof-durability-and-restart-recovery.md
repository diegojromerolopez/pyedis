# US-001 — AOF Durability and Restart Recovery

**change_type:** new  
**depends_on:** ["US-001"]

## User Story
As an operator, I want durable append-only state with absolute expirations and safe restart recovery so that successful mutations survive process termination without reviving expired keys.

## Requirements and Atomic Tasks

1. Implement `src/persistence.py` for JSON-lines AOF append, configurable fsync, replay, absolute expiration handling, corrupt trailing-line tolerance, and FLUSHALL truncation. Add `tests/unit/test_persistence.py` with temporary directories, fake clocks, injected file boundaries, and restart round trips.
2. Compose persistence into `src/main.py` and commands, then extend `tests/integration/test_server.py` and `tests/e2e/run_tests.sh` with restart, SIGKILL-like recovery, fsync ordering, corrupt-tail, expiration-during-downtime, and FLUSHALL scenarios.

## Definition of Done (DoD)

- Every successful SET, DEL, INCR, DECR, and positive EXPIRE mutation appends exactly one valid JSON line with the required operation and absolute `expire_at` where applicable. Failed conditionals, reads, and missing-key operations append nothing. Non-positive EXPIRE records an immediately expired absolute timestamp when it deletes a key. FLUSHALL truncates `dump.aof` to zero bytes and leaves no retained record.
- With `PYEDIS_AOF_FSYNC=true`, flush and `os.fsync` occur before the success RESP reply is transmitted; false skips fsync while preserving append correctness. Startup creates the data directory when possible, replays records in order, and evicts records expired at the injected/current clock.
- A malformed or truncated final JSON line logs exactly `pyedis: ignoring corrupt trailing AOF line` and preserves all preceding valid state. Non-trailing corruption fails startup with a `pyedis: ` diagnostic and exit 1. Absolute timestamps are never replaced by relative TTL values during replay.
- Dedicated executable black-box scenarios cover SET, DEL, INCR, DECR, EXPIRE, FLUSHALL persistence, restart GET/TTL, expiration during downtime, corrupt trailing line, fsync ordering, and data-directory failure. They physically execute client commands, poll readiness, and assert domain payloads and exit status; no static sleep or connect-only test is accepted.
- Persistence tests use temporary directories, fake clocks, in-memory stores, and injected logger/file seams. All time assertions are deterministic. `unittest` only is permitted; pytest and all third-party test frameworks/artifacts are forbidden. No stubs, placeholders, tautological tests, `|| true`, or masked failures are allowed.
- Required paths are `src/persistence.py`, `src/main.py`, `tests/unit/test_persistence.py`, `tests/integration/test_server.py`, `tests/e2e/Dockerfile`, `tests/e2e/run_tests.sh`, `docker-compose.yml`, and all pinned paths from prior stories. Docker commands use `docker compose -f docker-compose.yml ...`, never `docker-compose`.
- `make test` passes every unit and integration scenario. Full lint, coverage, documentation, and final e2e gates are enforced by US-005.

```noctifab-contract
{
  "story_id": "US-001",
  "public_contracts": [
    {
      "id": "aof.restart-recovery",
      "interface": "PYEDIS_DATA_DIR/dump.aof plus TCP RESP2 server",
      "applicable_path_prefixes": ["src/persistence.py", "src/main.py", "tests/", "docker-compose.yml"],
      "allowed_executables": ["python3 -m src.main", "make e2e"],
      "exit_codes": [0, 1],
      "stdout_contains": [],
      "stderr_prefixes": ["pyedis: "]
    }
  ]
}
```
