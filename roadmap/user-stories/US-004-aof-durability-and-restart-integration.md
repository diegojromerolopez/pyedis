# US-004 — AOF Durability, Restart Recovery & Deployment Integration

**depends_on:** ["US-001"]  
**change_type:** new

## User story
As an operator, I want durable mutations and restart recovery so that values and absolute expirations survive normal shutdown, SIGKILL, and process restart without reviving expired keys.

## Requirements and atomic tasks

1. Implement `src/persistence.py` for JSON-line AOF append, optional fsync, replay, absolute expiration timestamps, corrupt trailing-line recovery, and FLUSHALL truncation; co-locate `tests/unit/test_persistence.py` using temporary directories and fake clocks.
2. Integrate persistence into the real server and produce `README.md`, `docs/index.md`, `docs/api.md`, `.readthedocs.yaml`, Compose services, and `tests/e2e/Dockerfile` plus `tests/e2e/run_tests.sh`; add restart, fsync ordering, redis-py, and redis-cli scenarios in `tests/integration/test_server.py`.

## Definition of Done (DoD)

- Every successful SET, effective DEL, INCR, DECR, EXPIRE, and FLUSHALL appends exactly one valid JSON line with the specified operation schema. No-op conditional SET, missing DEL, and missing EXPIRE append nothing.
- SET records `expire_at` as an absolute timestamp or null; EXPIRE records an absolute timestamp. Replay never converts absolute timestamps back into renewed relative lifetimes.
- With `PYEDIS_AOF_FSYNC=true`, fsync occurs after the mutation record and before the corresponding RESP reply is transmitted. False skips fsync while still writing the record.
- Startup replays valid records sequentially, removes already-expired records using an injected/current clock, ignores only a corrupt or truncated final line while logging exactly `pyedis: ignoring corrupt trailing AOF line`, and treats a corrupt non-final line as a prefixed fatal startup error.
- FLUSHALL removes state and truncates `data/dump.aof` to zero bytes. Restart tests verify values, counters, persistent keys, live TTLs, expired TTLs, and SIGKILL-style trailing corruption behavior.
- `docker-compose.yml` and `docker-compose.e2e.yml` define `api` and `e2e`; `make e2e` uses the Docker CLI v2 command `docker compose -f docker-compose.e2e.yml up --build --exit-code-from e2e`. The E2E container uses `redis-cli`, readiness polling, `set -eu`, real assertions, and no static sleep-only readiness.
- Dedicated black-box scenarios exercise every supported command, AOF restart, absolute expiration during downtime, FLUSHALL truncation, malformed trailing line, redis-py pipeline, concurrency, and redis-cli compatibility. Each scenario asserts actual response payloads and exit behavior.
- Required documentation explicitly covers installation, running, all command contracts, RESP envelopes, AOF schema, architecture, expiration, persistence, deployment, and `make test`, `make lint`, and `make e2e`.
- Tests remain standard-library unittest except the explicitly permitted redis-py/redis-cli client tools used for integration/E2E. Pytest is forbidden. No stubs, shell error masking, or tautological tests exist. All tests pass with exit code `0`; intermediate linting is advisory.

```noctifab-contract
{"story_id": "US-004","public_contracts":[{"id":"aof.restart-durability","interface":"TCP server with PYEDIS_DATA_DIR/dump.aof and Docker Compose E2E","applicable_path_prefixes":["src/persistence.py","src/main.py","tests/","docs/","docker-compose.e2e.yml"],"allowed_executables":["python3 -m src.main","make e2e","redis-cli"],"exit_codes":[0,1],"stdout_contains":[],"stderr_prefixes":["pyedis: "]}]}
```