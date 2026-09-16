# Task: Complete build, Compose, and black-box verification scaffolding

- **ID**: `US-001-TASK-003`
- **Story ID**: `US-001`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-002`
- **Target Files**: `Makefile`, `.gitignore`, `docker-compose.yml`, `docker-compose.e2e.yml`, `tests/e2e/Dockerfile`, `tests/e2e/run_tests.sh`, `tests/integration/test_server.py`, `tests/integration/test_packaging.py`, `src/main.py`, `src/runtime.py`

## Description

Complete the repository-facing operational slice without changing the public TCP contract. Add Makefile with `make test` exactly invoking `python3 -m unittest discover -s tests -v`, failing when no tests are discovered, and `make e2e` based on `docker compose -f docker-compose.e2e.yml up --build --exit-code-from e2e`. Add .gitignore, docker-compose.yml, docker-compose.e2e.yml, tests/e2e/Dockerfile, and executable tests/e2e/run_tests.sh. The normal Compose service must run python3 -m src.main and expose the configured port; the e2e service must run a standard-library-only black-box harness. Implement or complete that harness so it starts the process, polls the TCP socket for readiness instead of sleeping statically, sends RESP and inline PING, asserts exact +PONG\\r\\n replies, and launches a malformed-configuration case that exits nonzero and emits the `pyedis: ` stderr prefix. Ensure shell failures propagate nonzero, there are no masked pipelines, stubs, pass statements, ellipses, or third-party test imports, and all required files exist. Add co-located unittest coverage for the Makefile/Compose contract or invoke the actual commands in the containerized e2e path; do not require host installations of Docker utilities beyond the declared Compose runner.
