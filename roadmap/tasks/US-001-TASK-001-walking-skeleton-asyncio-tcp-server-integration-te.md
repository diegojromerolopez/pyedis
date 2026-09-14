# Task: Walking Skeleton AsyncIO TCP Server & Integration Test

- **ID**: `US-001-TASK-001`
- **Story ID**: `US-001`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `[]` 
- **Target Files**: `pyproject.toml`, `requirements.txt`, `Makefile`, `src/main.py`, `tests/integration/test_server.py`

## Description

Create project environment configuration files (pyproject.toml, requirements.txt, Makefile) and implement a thin-shell asyncio TCP server in src/main.py listening on port 6379 (or PORT env var) that responds to basic 'PING' commands with '+PONG\r\n'. Create an integration characterization test in tests/integration/test_server.py using unittest.IsolatedAsyncioTestCase to verify server socket connection and PING/PONG handling. Ensure zero dependencies on pytest.
