# Task: QA Remediation: Implement Missing Features for US-002

- **ID**: `qa-remediation-us-002-2`
- **Story ID**: `US-002`
- **Status**: `SUCCESS`
- **Change Type**: ``
- **Depends On**: `US-002-TASK-001`, `US-002-TASK-002`, `US-002-TASK-003`, `qa-remediation-us-002-1`

## Description

QA Acceptance Review detected missing or incomplete features for US-002:
- Fix `client_session` in `src/server.py` to be declared as `async def client_session`.
- Fix exception handler binding in `client_session` from `except (...)` to `except (...) as exc:` to avoid referencing undefined `_` variable.
- Ensure clean connection closure and protocol errors return RESP error responses without raising NameError or crashing the session task.

Summary: US-002 fails QA acceptance verification. The function `client_session` in `src/server.py` is defined as a synchronous function (`def`) containing `await` expressions, which causes a SyntaxError, and its exception handler references an undefined variable `_` instead of binding `as exc`, causing a NameError on client disconnect or malformed RESP requests.

Implement the missing functionality and verify with tests.
