# Task: Static Analysis, Formatting, Coverage Gate & Makefile Targets

- **ID**: `US-005-TASK-001`
- **Story ID**: `US-005`
- **Status**: `PENDING`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`, `US-002-TASK-001`, `US-003-TASK-001`, `US-004-TASK-001`
- **Target Files**: `Makefile`, `pyproject.toml`, `tests/test_hardening.py`

## Description

Configure and enforce static analysis via `ruff check src tests` and `mypy --strict src` with 0 findings, and automated formatting via `ruff format src tests`. Ensure the Makefile includes all mandatory recipes (`install`, `run`, `test`, `lint`, `format`, `e2e`) exactly once. Write supplementary unit tests using standard library `unittest` to ensure total line coverage of `src/` reaches >= 95% when measured via `coverage run -m unittest discover -s tests`.
