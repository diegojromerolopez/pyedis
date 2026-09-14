# User Story 001: Legacy Codebase Characterization & Stabilization

**Story ID:** US-001  
**Title:** Legacy Codebase Characterization & Stabilization  
**depends_on:** []  
**change_type:** new  

## Description
As a developer, I want to establish characterization test suites and verify the existing legacy codebase infrastructure (`src/resp.py`, `src/store.py`, `src/commands.py`, `src/persistence.py`, `src/main.py`) so that future refactoring and feature extensions can proceed safely without regressions.

## Functional Requirements & Subsystems
1. **Walking Skeleton Verification:** Establish a thin, runnable TCP server entry point in `src/main.py` that listens on port `6379` (or `PORT` env var) and responds to basic `PING` commands with `+PONG\r\n`.
2. **Legacy Characterization Tests:** Create standard library `unittest` characterization tests covering existing module contracts in `tests/unit/` (`test_resp.py`, `test_store.py`, `test_commands.py`, `test_persistence.py`) and `tests/integration/test_server.py`.
3. **Forbidden Tooling Gate:** Guarantee zero dependencies on `pytest`. All tests MUST subclass `unittest.TestCase` or `unittest.IsolatedAsyncioTestCase` and be executable via `python3 -m unittest discover -s tests -v`.

## Definition of Done (DoD)
- **Observable Entrypoint Contract:** `python3 -m src.main` starts an asyncio TCP server accepting connections on default port `6379` or custom `PORT` environment variable.
- **Testing Framework Rule:** Zero `pytest` imports, dependencies, or configuration files (`conftest.py`, `pytest.ini`). Tests strictly use Python standard library `unittest`.
- **Testing Invariant:** All characterization tests pass with 100% pass rate using `python3 -m unittest discover -s tests -v`.
- **Pinned File Paths:** Required initial files exist: `pyproject.toml`, `requirements.txt`, `Makefile`, `src/main.py`, `src/resp.py`, `src/store.py`, `src/commands.py`, `src/persistence.py`.

```noctifab-contract
{
  "story_id": "US-001",
  "public_contracts": [{
    "id": "legacy.characterization",
    "interface": "Python Unittest Characterization Suite",
    "applicable_path_prefixes": ["src/", "tests/"],
    "allowed_executables": ["python3"],
    "exit_codes": [0],
    "stdout_contains": ["OK"],
    "stderr_prefixes": []
  }]
}
```