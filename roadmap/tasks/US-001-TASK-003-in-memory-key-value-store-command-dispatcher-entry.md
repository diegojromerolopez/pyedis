# Task: In-Memory Key-Value Store, Command Dispatcher & Entrypoint Integration

- **ID**: `US-001-TASK-003`
- **Story ID**: `US-001`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-002`
- **Target Files**: `src/store.py`, `src/commands.py`, `src/main.py`, `tests/unit/test_store.py`, `tests/unit/test_commands.py`

## Description

Implement `Store` class in `src/store.py` with `asyncio.Lock` concurrency protection and dependency-injected `Clock` (defaulting to `time.time`). Implement command dispatcher in `src/commands.py` with case-insensitive routing for: `PING` (with optional argument returning BulkString), `ECHO`, `QUIT` (returns `+OK\r\n` and signals socket closure), `SET` (basic key-value), `GET` (returns value or NullBulkString), `DEL` (returns count of removed keys), and `EXISTS` (returns sum of existing keys, duplicate-counted). Handle unrecognized commands (`-ERR unknown command '<NAME>'\r\n`) and arity violations (`-ERR wrong number of arguments for '<cmd>' command\r\n`). Integrate `store`, `commands`, and `resp` modules with `src/main.py` TCP server loop. Co-locate unit tests in `tests/unit/test_store.py` and `tests/unit/test_commands.py` using `unittest` and `unittest.mock` to verify full command dispatching and concurrency handling.
