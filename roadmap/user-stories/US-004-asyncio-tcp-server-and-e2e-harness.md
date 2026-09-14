# User Story 004: Asyncio TCP Server, Signal Handling, and Docker Compose E2E Black-Box Harness

**Story ID:** US-004  
**Title:** Asyncio TCP Server, Signal Handling, and Docker Compose E2E Black-Box Harness  
**depends_on:** ["US-002", "US-003"]  
**change_type:** new  

## Description
As a system administrator, I want an `asyncio` TCP server entrypoint with clean signal handling and a Docker Compose black-box verification harness so that client drivers (`redis-py`) and `redis-cli` can interact seamlessly with `pyedis`.

## Functional Requirements & Subsystems
1. **Asyncio TCP Server & Composition Root (`src/main.py`):**
   - Bind TCP server using `asyncio.start_server` on host `0.0.0.0` and port specified by `PORT` env var (default `6379`).
   - Handle `SIGINT` and `SIGTERM` signals cleanly: flush open files, close socket server, and exit code `0`.
   - Output operational diagnostic logs prefixed with `pyedis: `.
   - Thin entrypoint pattern delegating to `run_server` async function.
2. **E2E Black-Box Harness (`docker-compose.yml`, `tests/e2e/`):**
   - Define `docker-compose.yml` with `api` and `e2e` services.
   - `tests/e2e/Dockerfile`: `python:3.14-alpine` + `redis` (`redis-cli`).
   - `tests/e2e/run_tests.sh`: Black-box `redis-cli` assertions testing every command against `${REDIS_URL}` and exiting with `0` on success.

## Definition of Done (DoD)
- **Modern Docker Compose Subcommand:** `make e2e` invokes `docker compose up --build --exit-code-from e2e` using space-separated Docker CLI v2 syntax.
- **Integration Tests:** `tests/integration/test_server.py` tests concurrency (50 parallel client operations), pipelines, and process restarts using `redis-py`.
- **Clean Shutdown:** Signals (`SIGINT`/`SIGTERM`) exit cleanly with status `0` and flush pending AOF writes.

```noctifab-contract
{
  "story_id": "US-004",
  "public_contracts": [{
    "id": "server.e2e-harness",
    "interface": "Asyncio TCP Server & E2E Docker Harness",
    "applicable_path_prefixes": ["src/main.py", "docker-compose.yml", "tests/e2e/"],
    "allowed_executables": ["docker", "python3"],
    "exit_codes": [0],
    "stdout_contains": ["pyedis:"],
    "stderr_prefixes": []
  }]
}
```