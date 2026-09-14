# Task: Project Configuration, Static Analysis & Makefile Tooling

- **ID**: `US-003-TASK-001`
- **Story ID**: `US-003`
- **Status**: `PENDING`
- **Change Type**: `FEATURE`
- **Depends On**: `US-002-TASK-001`
- **Target Files**: `pyproject.toml`, `Makefile`

## Description

Configure pyproject.toml with PEP 621 metadata, [tool.ruff], and [tool.mypy] sections. Refactor all codebase type annotations to use standard PEP 585 built-in generic collections (dict, list, tuple, set) instead of typing module aliases. Ensure ruff check src tests and mypy --strict src pass with zero errors, warnings, or suppressions (# noqa or # type: ignore). Verify no source file in src/ exceeds 500 lines of code. Implement Makefile targets: install (python3 -m pip install -e ".[dev]"), run (python3 -m src.main), test (python3 -m unittest discover -s tests -v), lint (ruff check src tests && mypy --strict src), and format (ruff format src tests). Ensure pytest is strictly absent from all project configuration and dependencies.
