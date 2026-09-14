# User Story 005: Project Hardening, Maintenance Readiness & Code Quality

**Story ID:** US-005  
**Title:** Project Hardening, Maintenance Readiness & Code Quality  
**depends_on:** ["US-001", "US-002", "US-003", "US-004"]  
**change_type:** new  

## Description
As a maintainer, I want repository-wide linting, formatting, documentation, and 95%+ test coverage so that `pyedis` meets enterprise-grade quality standards.

## Functional Requirements & Subsystems
1. **Formatting & Static Analysis:**
   - Strict compliance with `ruff check src tests` and `mypy --strict src` with 0 findings.
   - Automated formatting via `ruff format src tests`.
2. **Code Coverage Gate:**
   - Total line coverage of `src/` must be >= 95% measured via standard library `unittest` coverage suite (`coverage run -m unittest discover -s tests`).
3. **Documentation:**
   - Complete `README.md` with usage instructions, command reference, and architecture summary.
   - Read the Docs setup with `.readthedocs.yaml`, `docs/index.md`, and `docs/api.md`.
4. **Makefile Recipes:**
   - Ensure all mandatory recipes (`install`, `run`, `test`, `lint`, `format`, `e2e`) are implemented exactly once.

## Definition of Done (DoD)
- **Zero Linter Findings:** `make lint` executes `ruff check src tests` and `mypy --strict src` with zero warnings or errors.
- **Coverage Threshold:** >= 95% code coverage across all modules in `src/` without using `pytest`.
- **Documentation Completeness:** `README.md`, `.readthedocs.yaml`, `docs/index.md`, and `docs/api.md` exist and reflect current architecture and RESP protocol behavior.

```noctifab-contract
{
  "story_id": "US-005",
  "public_contracts": [{
    "id": "hardening.maintenance",
    "interface": "Quality Assurance & Hardening Gate",
    "applicable_path_prefixes": ["src/", "tests/", "docs/"],
    "allowed_executables": ["make", "ruff", "mypy", "coverage"],
    "exit_codes": [0],
    "stdout_contains": ["OK"],
    "stderr_prefixes": []
  }]
}
```

## Refined Acceptance Criteria & Missing Requirements

The QA Acceptance Review identified the following incomplete features and requirements that MUST be implemented to satisfy the Definition of Done:

- [ ] **Missing Feature**: E2E test execution failure (docker compose -f docker-compose.e2e.yml up --build --exit-code-from test-runner): time="2026-09-14T22:21:36+02:00" level=warning msg="/Users/diegoj/repos/pyedis/docker-compose.e2e.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
no such service: test-runner: not found


**Audit Summary**: E2E test suite failed (docker compose -f docker-compose.e2e.yml up --build --exit-code-from test-runner): command execution failed: exit status 1 (output: time="2026-09-14T22:21:36+02:00" level=warning msg="/Users/diegoj/repos/pyedis/docker-compose.e2e.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
no such service: test-runner: not found
)
time="2026-09-14T22:21:36+02:00" level=warning msg="/Users/diegoj/repos/pyedis/docker-compose.e2e.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
no such service: test-runner: not found

