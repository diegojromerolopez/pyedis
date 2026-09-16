# US-001 — Walking Skeleton & Foundational Scaffolding

**depends_on:** []  
**change_type:** new

## User story
As an operator, I want a minimal runnable pyedis TCP process so that the repository can be built, started, health-checked, and extended safely.

## Requirements and atomic tasks

1. Create `pyproject.toml`, `requirements.txt`, `Makefile`, `src/__init__.py`, `src/main.py`, `tests/integration/test_server.py`, `.gitignore`, and the minimal Docker/Compose scaffolding. Task 1 must be a thin executable walking skeleton: `src/main.py` is under 15 lines and delegates immediately to a testable server factory/run function. It listens on `PORT`, accepts a RESP `PING`, and returns `+PONG\\r\\n`; include a real `unittest.IsolatedAsyncioTestCase` smoke test.
2. Add environment parsing, graceful SIGINT/SIGTERM shutdown, startup error handling, and a real socket readiness-polled smoke path. Co-locate tests for valid defaults, custom port, invalid configuration, bind failure, clean shutdown, and diagnostic prefixes.

## Definition of Done (DoD)

- `python3 -m src.main` starts a TCP server on `PORT` and a RESP array `*1\\r\\n$4\\r\\nPING\\r\\n` receives exactly `+PONG\\r\\n`; inline `PING\\r\\n` also receives that reply.
- `PORT`, `PYEDIS_DATA_DIR`, and `PYEDIS_AOF_FSYNC` are parsed with the specified defaults. Invalid values and bind/data-directory failures write `pyedis: <reason>` to stderr and exit `1`; clean signals exit `0`.
- Required paths created in this story are present: `pyproject.toml`, `requirements.txt`, `Makefile`, `.gitignore`, `src/__init__.py`, `src/main.py`, `tests/integration/test_server.py`, `docker-compose.yml`, `docker-compose.e2e.yml`, `tests/e2e/Dockerfile`, and `tests/e2e/run_tests.sh`.
- `make test` is exactly `python3 -m unittest discover -s tests -v`; zero discovered tests is a failure. `make e2e` is exactly based on `docker compose -f docker-compose.e2e.yml up --build --exit-code-from e2e`.
- Tests use only standard-library unittest and in-memory/test-double boundaries; no pytest or third-party test framework is imported or configured.
- No stubs, `pass`, ellipses, `NotImplementedError`, masked shell failures, or tautological assertions exist. The entrypoint delegates to testable code and does not contain the server implementation.
- Black-box validation starts the process, polls the socket rather than sleeping statically, sends both RESP and inline PING, asserts exact replies, and verifies a malformed startup configuration exits nonzero with the required stderr prefix.
- All tests pass with exit code `0` and all command failures use nonzero exit codes.

```noctifab-contract
{"story_id": "US-001","public_contracts":[{"id":"tcp.ping","interface":"TCP 127.0.0.1:${PORT} using RESP2 or inline commands","applicable_path_prefixes":["src/","tests/"],"allowed_executables":["python3 -m src.main"],"exit_codes":[0,1],"stdout_contains":[],"stderr_prefixes":["pyedis: "]}]}
```