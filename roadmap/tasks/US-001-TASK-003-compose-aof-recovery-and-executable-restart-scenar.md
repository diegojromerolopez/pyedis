# Task: Compose AOF recovery and executable restart scenarios

- **ID**: `US-001-TASK-003`
- **Story ID**: `US-001`
- **Status**: `PENDING`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-002`
- **Target Files**: `src/main.py`, `src/server.py`, `src/store.py`, `src/commands.py`, `src/persistence.py`, `tests/integration/test_server.py`, `tests/e2e/Dockerfile`, `tests/e2e/run_tests.sh`, `docker-compose.yml`, `Makefile`

## Description

Integrate the persistence component into src/main.py, server lifecycle, store, and command handlers. Route every successful SET, DEL, INCR, DECR, and EXPIRE mutation through one append operation with absolute expiration metadata; append before sending the successful RESP reply, and when PYEDIS_AOF_FSYNC=true guarantee flush and os.fsync complete before transmission. Make FLUSHALL truncate dump.aof and ensure startup creates the configured data directory when possible, replays records in order, and evicts keys expired during downtime. On startup errors, emit the required pyedis: diagnostic and exit 1. Extend tests/integration/test_server.py with real-process scenarios covering restart GET/TTL, all mutation types, failed conditional and missing-key no-op durability, expiration during downtime, corrupt trailing and non-trailing records, fsync ordering, FLUSHALL, and data-directory failure. Create or update tests/e2e/Dockerfile, tests/e2e/run_tests.sh, and docker-compose.yml for executable black-box tests that physically issue client commands, poll readiness, terminate processes in a SIGKILL-like manner, assert domain payloads and exit status, and never use static sleeps, connect-only checks, || true, or masked failures. Use docker compose -f docker-compose.yml commands and containerized tooling rather than host installations. Keep all tests unittest-compatible where applicable and verify make test passes the unit and integration suite.
