# Task: Establish thin server lifecycle walking skeleton

- **ID**: `US-002-TASK-001`
- **Story ID**: `US-002`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`
- **Target Files**: `src/main.py`, `src/server.py`, `tests/unit/test_main.py`

## Description

Create or preserve a primary entrypoint in src/main.py that is fewer than 15 lines and immediately delegates to a testable lifecycle function. Provide a minimal TCP server/application lifecycle capable of starting, accepting or initializing the protocol service, and shutting down deterministically without implementing command semantics yet. Characterize any existing main/module entrypoints before changing them, and add unittest smoke coverage that invokes the lifecycle in-process and verifies the allowed python3 -m src.main execution path exits cleanly. Keep stdout empty on success and prefix operational errors with 'pyedis: '. Do not install host dependencies; use only the standard library and, if an isolated runner is needed, a minimal containerized Python runner. This task must leave the project runnable for the subsequent RESP and dispatch slices.
