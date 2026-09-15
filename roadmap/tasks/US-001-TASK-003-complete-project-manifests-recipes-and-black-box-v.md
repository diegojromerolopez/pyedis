# Task: Complete project manifests recipes and black-box verification

- **ID**: `US-001-TASK-003`
- **Story ID**: `US-001`
- **Status**: `PENDING`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-002`
- **Target Files**: `pyproject.toml`, `requirements.txt`, `Makefile`, `tests/integration/test_server.py`, `src/main.py`

## Description

Add pyproject.toml, requirements.txt, and Makefile for the runnable project. Define build, install, run, test, lint, format, and e2e recipes; test must invoke `python3 -m unittest discover -s tests -v`, recipes must not use pytest or hyphenated docker-compose commands, and lint/format may be advisory while still avoiding shell error masking. Extend tests/integration/test_server.py with separate black-box E2E scenarios that launch `python3 -m src.main` on a dynamically selected PORT, poll socket readiness rather than sleeping blindly, exercise RESP PING, RESP message echo, inline PING, RESP framing, and invalid arity, then terminate and assert clean lifecycle/diagnostic behavior. Ensure required paths exist, the entrypoint remains under 15 lines where practical, runtime dependencies remain standard-library-only, and all tests execute deterministically with unittest. If an external runner is needed, use a minimal containerized runner rather than requiring host installations.
