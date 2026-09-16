# Task: Stabilize thin server entrypoint walking skeleton

- **ID**: `US-001-TASK-001`
- **Story ID**: `US-001`
- **Status**: `PENDING`
- **Change Type**: `FEATURE`
- **Depends On**: `[]` 
- **Target Files**: `src/main.py`, `src/server.py`, `src/commands.py`, `tests/integration/test_server.py`, `Makefile`

## Description

Inspect the existing legacy server and command entrypoints, then preserve their externally visible RESP2 behavior while making src/main.py a thin shell of fewer than 15 lines that immediately delegates to a testable core entrypoint function. Ensure python3 -m src.main remains runnable, accepts the existing environment/configuration conventions, starts a readiness-capable server, and exits with the documented diagnostic prefix on startup failures. Add or update characterization coverage in tests/integration/test_server.py for the existing entrypoint, basic command round trip, readiness polling, clean shutdown, and invalid startup configuration; tests must use unittest only, execute real entrypoint behavior, avoid static sleeps and connect-only assertions, and complete quickly. Do not implement AOF persistence yet, but expose a stable server construction/run seam that the persistence composition task can call.
