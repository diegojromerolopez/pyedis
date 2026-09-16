# Task: Add configuration and graceful process lifecycle

- **ID**: `US-001-TASK-002`
- **Story ID**: `US-001`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`
- **Target Files**: `src/main.py`, `src/config.py`, `src/server.py`, `src/runtime.py`, `tests/integration/test_server.py`, `tests/unit/test_config.py`, `tests/unit/test_runtime.py`

## Description

Extend the walking skeleton with production startup behavior and co-located tests. Implement parsing for PORT, PYEDIS_DATA_DIR, and PYEDIS_AOF_FSYNC with the specified repository defaults; validate types, ranges, allowed fsync values, and data-directory creation/availability. Add a testable application lifecycle/run boundary that installs SIGINT and SIGTERM handlers, closes the listening socket and active resources cleanly, and returns exit code 0 on clean signal termination. Convert invalid configuration, data-directory failures, and bind failures into concise stderr diagnostics beginning exactly with `pyedis: ` and return exit code 1 without masking the original reason. Preserve the thin src/main.py delegation and the PING protocol behavior. Expand tests in tests/integration/test_server.py or a nearby co-located unittest module to cover valid defaults, custom port, invalid configuration, an unwritable or invalid data directory using temporary test doubles, bind failure, clean shutdown, and diagnostic prefixes. Tests must remain standard-library unittest only and must exercise real sockets or explicit injectable boundaries rather than static sleeps.
