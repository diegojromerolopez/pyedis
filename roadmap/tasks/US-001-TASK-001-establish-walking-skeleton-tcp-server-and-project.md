# Task: Establish Walking Skeleton TCP Server and Project Configuration

- **ID**: `US-001-TASK-001`
- **Story ID**: `US-001`
- **Status**: `PENDING`
- **Change Type**: `FEATURE`
- **Depends On**: `[]` 
- **Target Files**: `pyproject.toml`, `requirements.txt`, `Makefile`, `src/main.py`, `tests/integration/test_server.py`

## Description

Set up foundational project configuration files (pyproject.toml, requirements.txt, Makefile) and implement a thin asyncio TCP server in src/main.py. The server must listen on default port 6379 or custom PORT environment variable and respond to basic PING commands with +PONG\r\n. Create an integration characterization test in tests/integration/test_server.py using standard library unittest.IsolatedAsyncioTestCase to verify TCP server execution and PING/PONG handling. Ensure zero pytest dependencies or conftest files.
