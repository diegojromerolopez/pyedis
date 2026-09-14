# User Story: Walking Skeleton, Wire Protocol & Core Key-Value Operations

**Story ID:** US-001
**Title:** Walking Skeleton, Wire Protocol & Core Key-Value Operations
**Depends On:** []
**Change Type:** new

## Description
As a backend client or system operator, I want a running, lightweight Redis-compatible TCP server (`pyedis`) executing on Python 3.14 that parses standard RESP2/RESP3 wire frames and inline commands, handles connection liveness (`PING`, `ECHO`, `QUIT`), and manages core key-value state (`SET`, `GET`, `DEL`, `EXISTS`).

## Tasks
1. **Thin Runnable TCP Entrypoint & PING Walking Skeleton:** Create `src/main.py` entrypoint, `Makefile`, `pyproject.toml`, `requirements.txt`, and basic `tests/unit/test_server_skeleton.py` unit/smoke test using `unittest.IsolatedAsyncioTestCase` verifying `PING` returns `+PONG\r\n` within 30 seconds.
2. **RESP Wire Protocol Engine (`src/resp.py`):** Implement streaming frame decoder, chunk reassembly, pipelined buffer parser, inline string decoder, and response frame encoders (`SimpleString`, `Error`, `Integer`, `BulkString`, `NullBulkString`, `Array`, `NullArray`). Co-locate unit tests in `tests/unit/test_resp.py` testing binary-safe inputs and fragmented TCP buffers.
3. **In-Memory Store & Core Dispatcher (`src/store.py`, `src/commands.py`):** Implement the `Store` class with `asyncio.Lock` concurrency protection and dependency-injected `Clock`, alongside `src/commands.py` dispatcher supporting case-insensitive command routing for `PING`, `ECHO`, `QUIT`, `SET` (basic key-value), `GET`, `DEL`, and `EXISTS`. Co-locate unit tests in `tests/unit/test_store.py` and `tests/unit/test_commands.py` using standard `unittest` and `unittest.mock`.

## Definition of Done (DoD)

### 1. Pinned Directory & Required File Layout
- The repository MUST implement the exact structure:
  - `pyproject.toml`
  - `requirements.txt`
  - `Makefile`
  - `README.md`
  - `.gitignore`
  - `src/__init__.py`, `src/main.py`, `src/resp.py`, `src/store.py`, `src/commands.py`
  - `tests/unit/test_resp.py`, `tests/unit/test_store.py`, `tests/unit/test_commands.py`
  - `data/`

### 2. Observable Entry Point & Black-Box Protocol Contracts
- Running `python3 -m src.main` listens on `127.0.0.1:${PORT:-6379}` over TCP.
- Standard Redis clients sending `PING\r\n` receive `+PONG\r\n`.
- Standard Redis clients sending `PING "hello world"\r\n` receive `$11\r\nhello world\r\n`.
- Executing `ECHO hello` receives `$5\r\nhello\r\n`.
- Executing `QUIT` returns `+OK\r\n` and immediately closes the TCP socket.
- Executing `SET key value` returns `+OK\r\n`.
- Executing `GET key` returns `$5\r\nvalue\r\n` (or `$-1\r\n` if key does not exist).
- Executing `DEL key1 key2` returns integer count of removed keys (e.g. `:2\r\n`).
- Executing `EXISTS key1 key1` returns duplicate-counted key existence sum (e.g. `:2\r\n`).

### 3. Anti-Stub & Anti-Gaming Invariant
- Stubs, `pass`, `...`, `NotImplementedError`, or tautological tests are strictly forbidden.
- All unit and integration tests MUST subclass standard library `unittest.TestCase` or `unittest.IsolatedAsyncioTestCase`.
- `pytest` is STRICTLY FORBIDDEN. No imports of `pytest`, no `conftest.py`, no `pytest.ini`.

### 4. Thin Shell Entrypoint Pattern
- `src/main.py` MUST be a thin entrypoint (< 15 lines) calling a testable server factory (`run_server(host, port, store, dispatcher)`).

### 5. Standard I/O & Output Formatting
- Unrecognized commands return `-ERR unknown command '<NAME>'\r\n`.
- Command arity violations return `-ERR wrong number of arguments for '<cmd>' command\r\n`.
- Server logs on stdout/stderr MUST use the prefix `pyedis: `.

### 6. Verification Criteria
- Running `make test` executes all unit tests via `python3 -m unittest discover -s tests -v` with zero failures.

```noctifab-contract
{
  "story_id": "US-001",
  "public_contracts": [
    {
      "id": "pyedis.tcp.ping",
      "interface": "TCP RESP Socket",
      "applicable_path_prefixes": ["src/"],
      "allowed_executables": ["python3 -m src.main"],
      "exit_codes": [0],
      "stdout_contains": ["pyedis:"],
      "stderr_prefixes": []
    }
  ]
}
```
