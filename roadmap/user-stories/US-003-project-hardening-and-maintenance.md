# User Story: Project Hardening, Maintenance Readiness & Code Quality

**Story ID:** US-003
**Title:** Project Hardening, Maintenance Readiness & Code Quality
**Depends On:** ["US-001", "US-002"]
**Change Type:** new

## Description
As a maintainer and release engineer, I want the `pyedis` codebase fully hardened with strict static analysis, complete test coverage, standardized Makefile execution targets, Read the Docs documentation, and a Docker E2E black-box test harness using standard `redis-cli`.

## Tasks
1. **Repository-Wide Formatting & Import Hygiene:** Configure PEP 621 `pyproject.toml` with `[tool.ruff]` and `[tool.mypy]`. Ensure built-in generic collections (`dict`, `list`, `tuple`, `set`) are used exclusively per PEP 585. Format code via `ruff format src tests`.
2. **Strict Static Analysis & Type Gate Compliance:** Enforce `ruff check src tests` and `mypy --strict src` with zero errors or suppressions (`# noqa` / `# type: ignore`). Ensure no source file exceeds 500 lines of code.
3. **Black-Box E2E Matrix Verification & Test Coverage Gate:** Create `docker-compose.yml`, `tests/e2e/Dockerfile`, and `tests/e2e/run_tests.sh`. Ensure `docker compose up --build --exit-code-from e2e` tests every command (`PING`, `ECHO`, `SET`, `GET`, `DEL`, `EXISTS`, `INCR`, `DECR`, `EXPIRE`, `TTL`, `KEYS`, `FLUSHALL`) via `redis-cli`. Verify line coverage $\ge 95\%$ across `src/` via `coverage run -m unittest discover -s tests`.
4. **Packaging, Read the Docs & Makefile Verification:** Create `.readthedocs.yaml`, `docs/index.md`, `docs/api.md`, and comprehensive `README.md`. Verify all Makefile targets (`install`, `run`, `test`, `lint`, `format`, `e2e`).

## Definition of Done (DoD)

### 1. Mandatory Makefile Targets
- `make install` → executes `python3 -m pip install -e ".[dev]"`.
- `make run` → executes `python3 -m src.main`.
- `make test` → executes `python3 -m unittest discover -s tests -v` with 0 failures.
- `make lint` → passes with ZERO findings for both `ruff check src tests` and `mypy --strict src`.
- `make format` → `ruff format src tests` formats code idempotently.
- `make e2e` → `docker compose up --build --exit-code-from e2e` passes with exit code 0.

### 2. E2E Black-Box Harness & Docker Compose
- Harness utilizes modern `docker compose` (space-separated CLI v2).
- `run_tests.sh` executes explicit assertions for each feature using `redis-cli` against `${REDIS_URL}` with zero failures.

### 3. Verification Gates
- Total line coverage of `src/` modules MUST be $\ge 95\%$.
- `pytest` is strictly absent from all dependencies and files.

```noctifab-contract
{
  "story_id": "US-003",
  "public_contracts": [
    {
      "id": "pyedis.quality.gate",
      "interface": "Makefile Validation Targets",
      "applicable_path_prefixes": ["src/", "tests/", "docs/"],
      "allowed_executables": ["make test", "make lint", "make e2e"],
      "exit_codes": [0],
      "stdout_contains": [],
      "stderr_prefixes": []
    }
  ]
}
```
