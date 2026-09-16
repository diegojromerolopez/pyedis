# Task: Compose AOF durability into commands and black-box restart scenarios

- **ID**: `US-001-TASK-003`
- **Story ID**: `US-001`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-002`
- **Target Files**: `src/main.py`, `src/server.py`, `src/commands.py`, `src/store.py`, `tests/integration/test_server.py`, `tests/e2e/Dockerfile`, `tests/e2e/run_tests.sh`, `docker-compose.yml`

## Description

Integrate the persistence component into src/main.py and the command execution path so every successful SET, DEL, INCR, DECR, and positive EXPIRE appends exactly one valid record, with absolute expire_at where applicable; failed conditionals, reads, and missing-key operations append nothing; non-positive EXPIRE records an immediately expired timestamp when it deletes a key; and FLUSHALL truncates the AOF. Enforce append/flush/fsync completion before sending a successful RESP reply when PYEDIS_AOF_FSYNC=true, while preserving correct append behavior when false. Add integration coverage for restart GET/TTL, SIGKILL-like termination and recovery, expiration during downtime, corrupt tails, fsync ordering, data-directory failure, and FLUSHALL. Extend tests/e2e/Dockerfile, tests/e2e/run_tests.sh, and docker-compose.yml with executable client-command scenarios that poll readiness, assert domain payloads and exit codes, and use 'docker compose -f docker-compose.yml ...' only. Do not use static sleeps, connect-only checks, pytest, redis-cli, '|| true', masked failures, or host package installation; if an external runner is needed, use a minimal containerized runner. Keep all prior characterization tests passing.
