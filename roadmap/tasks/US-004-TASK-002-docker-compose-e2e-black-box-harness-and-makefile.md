# Task: Docker Compose E2E Black-Box Harness and Makefile Target

- **ID**: `US-004-TASK-002`
- **Story ID**: `US-004`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-004-TASK-001`
- **Target Files**: `docker-compose.yml`, `tests/e2e/Dockerfile`, `tests/e2e/run_tests.sh`, `Makefile`

## Description

Create `docker-compose.yml` configuring the `api` service (building and running `pyedis`) and `e2e` test service. Write `tests/e2e/Dockerfile` based on `python:3.14-alpine` with `redis` (`redis-cli`) installed. Write `tests/e2e/run_tests.sh` executing black-box `redis-cli` assertions against `${REDIS_URL}` for basic commands, pipelining, and edge cases, exiting 0 on success. Add or update `Makefile` to include an `e2e` target that executes `docker compose up --build --exit-code-from e2e` using modern Docker CLI v2 syntax.
