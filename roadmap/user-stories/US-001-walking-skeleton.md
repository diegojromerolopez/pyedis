# US-001 — RESP Walking Skeleton and Project Scaffolding

**change_type:** new  
**depends_on:** []

## User story
As an operator, I want a runnable pyedis TCP process with a real RESP `PING` health path so that the project can be built, started, and validated before deeper command, storage, or persistence work.

## Requirements and atomic tasks
1. Create the thin `src/main.py` entrypoint, `pyproject.toml`, `requirements.txt`, `Makefile`, `.gitignore`, and `src/__init__.py`. The first implementation must be a minimal end-to-end asyncio server that accepts a RESP array or inline `PING`, returns `+PONG\\r\\n`, and has one co-located `unittest` socket smoke test runnable in under 30 seconds. Do not implement persistence or a broad command hierarchy in this task.
2. Add the initial `src/resp.py` framing boundary and expand the co-located unit/integration tests to prove one complete RESP request/reply, inline `PING`, case-insensitive command recognition, clean startup, and deterministic shutdown.

## Definition of Done (DoD)
- Observable entrypoints are `python3 -m src.main`, `make run`, and a TCP listener on `PORT`, default 6379. RESP requests and replies use CRLF exactly; `PING` returns `+PONG\\r\\n` and no command writes diagnostics to stdout.
- `src/main.py` is a thin wrapper under 15 lines delegating to a testable entrypoint. Required paths created now are `pyproject.toml`, `requirements.txt`, `Makefile`, `.gitignore`, `src/__init__.py`, `src/main.py`, `src/resp.py`, `tests/unit/test_resp.py`, `tests/integration/test_server.py`, `README.md`, `docs/index.md`, `docs/api.md`, `.readthedocs.yaml`, `docker-compose.e2e.yml`, `docker-compose.yml`, `src/store.py`, `src/commands.py`, `src/persistence.py`, `tests/unit/test_store.py`, `tests/unit/test_commands.py`, `tests/unit/test_persistence.py`, `tests/e2e/Dockerfile`, and `tests/e2e/run_tests.sh`; later files may initially contain only real minimal functionality, never stubs.
- `make test` invokes exactly `python3 -m unittest discover -s tests -v`; zero discovered tests is failure. Tests are Chicago-school `unittest` tests using injected/in-memory boundaries, not pytest or another framework.
- No pytest import, dependency, configuration, invocation, `pass`, ellipsis body, `NotImplementedError`, shell error masking, or tautological assertion exists. Runtime dependencies are standard library only.
- Edge cases covered are fragmented TCP input, inline versus array `PING`, lowercase/mixed-case command names, an empty request, malformed input, port binding failure, and orderly SIGINT/SIGTERM. Fatal startup errors use stderr prefix `pyedis: ` and exit 1; clean shutdown exits 0.
- The smoke test physically opens a socket, sends a command, asserts the exact payload, and polls readiness rather than sleeping. It does not merely import modules or connect/disconnect.
- `make test` passes 100%; intermediate linting is advisory, while final hardening owns the lint gate.

```noctifab-contract
{
  "story_id": "US-001",
  "public_contracts": [{
    "id": "resp.ping-health",
    "interface": "TCP RESP2/inline server at 127.0.0.1:PORT",
    "applicable_path_prefixes": ["src/", "tests/"],
    "allowed_executables": ["python3 -m src.main", "make run"],
    "exit_codes": [0, 1],
    "stdout_contains": [],
    "stderr_prefixes": ["pyedis: "]
  }]
}
```