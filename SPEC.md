# `pyedis` Specification: Native Redis RESP Key-Value Store in Python 3.14

## 1. Overview & Architectural Goals

`pyedis` is a high-performance, in-memory key-value store with a **native Redis wire-protocol (RESP2/RESP3) API exposed over TCP** (default port `6379`), written in modern Python (3.14 / 3.10+) with strict static typing (`mypy --strict src`) and standard library tooling. It mirrors Redis core command semantics (`PING`, `ECHO`, `QUIT`, `SET`, `GET`, `DEL`, `EXISTS`, `INCR`, `DECR`, `EXPIRE`, `TTL`, `KEYS`, `FLUSHALL`) with deterministic RESP reply and error envelopes, and persists state to an append-only file (AOF) using absolute expiration timestamps so data and TTLs survive process restarts and sudden terminations (`SIGKILL`). Standard Redis client utilities (`redis-cli`, `redis-py` v5+) MUST be 100% compatible with `pyedis`.

`pyedis` exercises the Python ecosystem seams: async TCP socket streams (`asyncio.start_server`), zero-copy stream parsing, dependency injection (clock + store + AOF logger), absolute timestamp durability, and lock-protected async concurrency.

> [!IMPORTANT]
> **STRICT TESTING MANDATE: ZERO PYTEST USAGE (STANDARD LIBRARY `unittest` ONLY)**
> - **`pytest` is STRICTLY FORBIDDEN:** The project MUST NOT use `pytest` under ANY circumstances.
> - **Zero `pytest` Dependencies or Artifacts:** Do NOT import `pytest`, do NOT list `pytest` in `requirements.txt` or `pyproject.toml`, do NOT create `conftest.py` or `pytest.ini`, and do NOT invoke `pytest` anywhere in Makefiles, scripts, or story contracts.
> - **Standard Library `unittest` Structure:** All unit and integration test classes MUST explicitly subclass `unittest.TestCase` (or `unittest.IsolatedAsyncioTestCase` for async test cases).
> - **Standard Library Mocking:** All test mocks MUST use `unittest.mock` (`MagicMock`, `AsyncMock`, `patch`).
> - **Standard Discovery Invocation:** All test suites MUST be executed via `python3 -m unittest discover -s tests -v` (wired to `make test`).

### Key Architectural Invariants
1. **Native RESP2/RESP3 Protocol:** True binary-safe Redis serialization protocol framing supporting both multi-bulk arrays and whitespace-delimited inline commands.
2. **Zero External Framework Dependencies:** Pure standard library async TCP networking (`asyncio.start_server`). No FastAPI, Starlette, Uvicorn, or web frameworks.
3. **Deterministic Dependency Injection:** The in-memory store accepts an injected `Clock` callable (`Callable[[], float]`), allowing unit tests to freeze, step, and fast-forward time deterministically without `sleep()` delays.
4. **Absolute Expiration Durability:** AOF records store absolute Unix epoch timestamps (`expire_at`), ensuring expired keys are never resurrected across server reboots.
5. **Strict Typing & Zero Linter Warnings:** Full PEP 585 built-in generic collections (`dict`, `list`, `tuple`, `set`). Must pass `ruff check src tests` and `mypy --strict src` with zero findings.
6. **500-Line Limit Rule:** No single Python source file (`.py`) may exceed 500 lines of code.

---

## 2. Directory Layout & Module Responsibilities

```
pyedis/
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI workflow (triggers on every push; runs lint, unit, e2e)
├── pyproject.toml            # PEP 621 metadata; deps, [tool.mypy], [tool.ruff] (NO pytest)
├── requirements.txt          # Pinned runtime + dev dependencies (NO pytest)
├── Makefile                  # install, run, test, lint, format, e2e targets
├── README.md                 # Project overview, installation, use cases, command ref, Redis compatibility
├── .readthedocs.yaml         # Read the Docs configuration file
├── docs/                     # Read the Docs documentation directory
│   ├── index.md              # Documentation entry point, installation, use cases & architecture
│   └── api.md                # Supported operations, RESP protocol specification, Redis compatibility level
├── .gitignore                # Ignores __pycache__/, .venv/, data/, .coverage, htmlcov/
├── Dockerfile.e2e            # Alpine-based container for black-box E2E validation
├── docker-compose.e2e.yml    # Black-box E2E multi-container test harness
├── .noctifab/
│   ├── config.yaml           # Noctifab orchestrator configuration
│   └── .gitignore            # Noctifab runtime artifacts ignore file
├── src/
│   ├── __init__.py           # Package marker & exported public interfaces
│   ├── main.py               # Asyncio TCP server entrypoint & signal handlers (SIGINT/SIGTERM)
│   ├── resp.py               # RESP wire protocol encoder & streaming chunk decoder
│   ├── store.py              # In-memory key-value store, expiration index, DI clock, async lock
│   ├── commands.py           # Command dispatcher, arity/syntax validation, error envelopes
│   └── persistence.py        # AOF append logger (absolute expire_at) & startup replay engine
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_store.py     # Store operations with injected deterministic mock clock (unittest.TestCase)
│   │   ├── test_resp.py      # RESP frame encoding, streaming chunk reassembly, pipelined buffers (unittest.TestCase)
│   │   ├── test_commands.py  # Arity, unknown commands, case-insensitivity, NX/XX, EX/PX (unittest.TestCase)
│   │   └── test_persistence.py  # AOF round-trip: write, absolute TTL replay, corrupt line recovery (unittest.TestCase)
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_server.py    # Live TCP socket tests via redis-py & raw sockets (unittest.IsolatedAsyncioTestCase)
│   └── e2e/
│       └── run_tests.sh      # Executable black-box redis-cli assertions against live server
└── data/                     # Runtime AOF storage directory (git-ignored)
```

---

## 3. Explicit Public API Signatures & Architectural Contracts

### 3.1 Protocol Module (`src/resp.py`)
```python
"""RESP wire protocol encoder and streaming decoder."""
from typing import Any

def encode_simple_string(s: str) -> bytes:
    """Encodes a string as a RESP Simple String (+<string>\r\n)."""
    ...

def encode_error(msg: str, err_type: str = "ERR") -> bytes:
    """Encodes an error as a RESP Error (-<TYPE> <msg>\r\n)."""
    ...

def encode_integer(n: int) -> bytes:
    """Encodes an integer as a RESP Integer (:<number>\r\n)."""
    ...

def encode_bulk_string(data: bytes | str | None) -> bytes:
    """Encodes bytes/string as a RESP Bulk String ($<len>\r\n<data>\r\n or $-1\r\n for None)."""
    ...

def encode_array(items: list[Any] | None) -> bytes:
    """Encodes a list as a RESP Array (*<count>\r\n<elem1>... or *-1\r\n for None)."""
    ...

def encode_resp(value: Any) -> bytes:
    """Polymorphic RESP serializer mapping Python types to RESP byte frames."""
    ...

def decode_resp_stream(buffer: bytearray) -> tuple[list[list[bytes]], bytearray]:
    """
    Parses all complete RESP commands (multi-bulk arrays and inline commands) from the buffer.
    Returns (parsed_commands, unparsed_remaining_bytes).
    Does not raise on partial buffers; partial frames remain in unparsed_remaining_bytes.
    """
    ...
```

### 3.2 In-Memory Store Module (`src/store.py`)
```python
"""In-memory key-value storage with active/lazy expiration and injected clock."""
import asyncio
import time
from collections.abc import Callable

Clock = Callable[[], float]

class Store:
    def __init__(self, clock: Clock = time.time) -> None:
        self._data: dict[str, str] = {}
        self._expires: dict[str, float] = {}  # key -> absolute unix epoch expiration
        self._clock: Clock = clock
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock

    def get(self, key: str) -> str | None:
        """Retrieves key value, lazily evicting if expired."""
        ...

    def set(self, key: str, value: str, expire_at: float | None = None,
            nx: bool = False, xx: bool = False) -> bool:
        """Sets key value with optional absolute expiration and existence conditions."""
        ...

    def delete(self, *keys: str) -> int:
        """Deletes keys, returning count of existing keys deleted."""
        ...

    def exists(self, *keys: str) -> int:
        """Returns count of existing keys among arguments."""
        ...

    def incr_by(self, key: str, delta: int) -> int:
        """Increments key integer value by delta, initializing to '0' if missing. Preserves TTL."""
        ...

    def expire(self, key: str, seconds: float) -> bool:
        """Sets TTL on key in seconds from current clock. If seconds <= 0, deletes key immediately."""
        ...

    def ttl(self, key: str) -> int:
        """Returns -2 (missing/expired), -1 (exists no TTL), or positive remaining seconds."""
        ...

    def keys(self, pattern: str) -> list[str]:
        """Performs active sweep, then returns all keys matching glob pattern (*, ?, [abc])."""
        ...

    def flushall(self) -> None:
        """Clears all keys and expirations."""
        ...
```

### 3.3 Persistence Module (`src/persistence.py`)
```python
"""Append-Only File (AOF) durability engine with absolute timestamps."""
from pathlib import Path
from typing import Any
from src.store import Store

class AOFLogger:
    def __init__(self, filepath: str | Path, fsync: bool = True) -> None:
        self.filepath: Path = Path(filepath)
        self.fsync: bool = fsync
        ...

    def log_mutation(self, record: dict[str, Any]) -> None:
        """Appends JSON line mutation to dump.aof and calls os.fsync if enabled."""
        ...

    def truncate(self) -> None:
        """Truncates dump.aof to 0 bytes on disk (FLUSHALL)."""
        ...

def replay_aof(filepath: str | Path, store: Store) -> int:
    """
    Sequentially replays dump.aof into store.
    Tolerates truncated/corrupt trailing line caused by abrupt crash (SIGKILL).
    Returns count of successfully replayed records.
    """
    ...
```

### 3.4 Command Dispatcher Module (`src/commands.py`)
```python
"""Command validation, execution routing, and RESP envelope generation."""
from src.store import Store
from src.persistence import AOFLogger

class CommandDispatcher:
    def __init__(self, store: Store, aof: AOFLogger | None = None) -> None:
        self.store: Store = store
        self.aof: AOFLogger | None = aof

    async def dispatch(self, args: list[bytes]) -> tuple[bytes, bool]:
        """
        Validates syntax/arity, routes command (case-insensitively), performs mutation,
        logs to AOF, and returns (resp_reply_bytes, should_close_connection).
        """
        ...
```

### 3.5 Server Entrypoint Module (`src/main.py`)
```python
"""Asyncio TCP server entrypoint and graceful signal handling."""
import asyncio

async def run_server(host: str = "0.0.0.0", port: int = 6379,
                       data_dir: str = "./data", fsync: bool = True) -> None:
    """
    Starts the TCP server loop:
    1. Creates `data_dir` via `os.makedirs(data_dir, exist_ok=True)` — MUST NOT assume it exists.
    2. Replays AOF from `<data_dir>/dump.aof` into the store (if the file exists).
    3. Registers SIGINT/SIGTERM handlers for graceful shutdown.
    4. Calls `asyncio.start_server` and serves forever.
    """
    ...

def main() -> None:
    """CLI entrypoint reading PORT, PYEDIS_DATA_DIR, PYEDIS_AOF_FSYNC from environment."""
    ...

if __name__ == "__main__":
    main()
```

---

## 4. Toolchain, Invocation, Exit Codes & Configuration

### 4.1 Runtime & Dev Dependencies
- **Runtime:** Standard Python 3.14+ library (`asyncio`, `dataclass`, `os`, `sys`, `time`, `typing`, `pathlib`, `json`, `signal`, `fnmatch`). No external web frameworks.
- **Dev:** `redis>=5.0`, `ruff>=0.8`, `mypy>=1.13`, `coverage>=7.6`. (NO `pytest`).
- **Testing Framework Rule (MANDATORY):** Tests MUST NOT use `pytest` or any third-party test framework under any circumstances. All unit and integration tests MUST be written using Python's standard library `unittest` framework (using `unittest.TestCase`, `unittest.IsolatedAsyncioTestCase` for async tests, and `unittest.mock`). All test modules must be executable via `python3 -m unittest discover -s tests`.
- **`pyproject.toml` Toolchain Configuration (MANDATORY):** Generators MUST emit a `pyproject.toml` containing exactly the following tool sections — no deviations:
  ```toml
  [tool.mypy]
  strict = true
  python_version = "3.12"
  exclude = ["tests/"]

  [tool.ruff]
  line-length = 100
  target-version = "py310"

  [tool.ruff.lint]
  select = ["E", "F", "I", "UP", "B", "C4", "PIE", "SIM"]
  ```
  `mypy` is run with `--strict src` (source only). `ruff` checks both `src` and `tests`.

### 4.2 Makefile Targets
Every target below is REQUIRED. The Makefile MUST use these exact commands — do not substitute alternatives:
```makefile
.PHONY: install run test lint format e2e clean

install:
	python3 -m pip install -e ".[dev]"

run:
	python3 -m src.main

test:
	python3 -m unittest discover -s tests -v

lint:
	ruff check src tests
	mypy --strict src

format:
	ruff format src tests

e2e:
	docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from test-runner-e2e

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache htmlcov .coverage
```
Note: All E2E testing tools (including `redis-cli`) run strictly inside the containerized test runner service; NO host system package installation is required.

### 4.3 Configuration Environment Variables
- `PORT` (default `6379`): TCP listen port for the RESP server.
- `PYEDIS_DATA_DIR` (default `./data`): Directory holding the `dump.aof` file.
- `PYEDIS_AOF_FSYNC` (default `true`): If `true`, calls `os.fsync` on the open AOF file descriptor after every state mutation before sending the RESP reply.

### 4.4 Exit Codes & Logging
- **Clean Shutdown (`SIGINT`/`SIGTERM`):** Server flushes open files, closes the TCP server socket, disconnects clients, and exits `0`.
- **Fatal Startup Error (e.g. port bound, uncreatable directory):** Log `pyedis: <reason>` to stderr and exit `1`.
- **Operational Diagnostic Logging:** All operational logs on stdout/stderr MUST use the prefix `pyedis: `.

### 4.5 Continuous Integration (`.github/workflows/ci.yml`)
A GitHub Actions CI workflow MUST be configured in `.github/workflows/ci.yml` that:
- **Trigger Strategy:** Executes automatically on **every push** to any branch (`on: push`) as well as on all pull requests (`on: pull_request`).
- **Automated Verification Pipeline:**
  1. **Checkout & Python Setup:** Checks out the codebase and provisions Python (3.12+ / 3.14).
  2. **Dependency Installation:** Installs runtime and development dependencies cleanly (`make install` or `pip install -r requirements.txt`).
  3. **Lint & Static Type Verification:** Executes `make lint` (`ruff check src tests` and `mypy --strict src`), requiring zero findings.
  4. **Unit & Integration Test Execution:** Executes `make test` (`python3 -m unittest discover -s tests -v`), verifying all unit and integration test suites pass with 100% success rate.
  5. **Containerized E2E Black-Box Test Execution:** Executes `make e2e` (`docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from test-runner-e2e`), ensuring the end-to-end black-box CLI test suite against the live containerized server succeeds completely.
- **Mandatory Pipeline Gate:** Linters, unit/integration tests, and containerized E2E black-box tests MUST all run and succeed with exit code 0 on every push for CI to pass.

---

## 5. RESP Wire Protocol & Framing Engine

`pyedis` communicates exclusively via standard REdis Serialization Protocol (RESP2/RESP3) over TCP.

### 5.1 RESP Frame Types & Wire Envelopes

| Frame Type | Byte Prefix | Wire Format | Example Wire Bytes | Decoded Representation |
| :--- | :---: | :--- | :--- | :--- |
| **Simple String** | `+` | `+<string>\r\n` | `+OK\r\n`, `+PONG\r\n` | `"OK"`, `"PONG"` |
| **Error** | `-` | `-<TYPE> <message>\r\n` | `-ERR syntax error\r\n` | `RedisError("ERR syntax error")` |
| **Integer** | `:` | `:<signed_number>\r\n` | `:1\r\n`, `:0\r\n`, `:-1\r\n`, `:-2\r\n` | `1`, `0`, `-1`, `-2` |
| **Bulk String** | `$` | `$<length>\r\n<data>\r\n` | `$5\r\nhello\r\n`, `$0\r\n\r\n` | `b"hello"`, `b""` |
| **Null Bulk String** | `$` | `$-1\r\n` | `$-1\r\n` | `None` (nil reply in RESP2) |
| **Array** | `*` | `*<count>\r\n<elem_1>...` | `*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n` | `[b"foo", b"bar"]` |
| **Empty Array** | `*` | `*0\r\n` | `*0\r\n` | `[]` (empty list) |
| **Null Array** | `*` | `*-1\r\n` | `*-1\r\n` | `None` (nil array) |

### 5.2 Stream Parsing, Fragmentation, Pipelining & Inline Commands
1. **TCP Stream Buffering & Chunking:** TCP provides a continuous stream with no packet boundary guarantees. The RESP decoder must accumulate incoming chunks in a stream buffer and yield parsed commands only when complete payloads (matching byte lengths and terminating `\r\n`) are received. Incomplete frames must remain buffered without blocking or crashing.
2. **Command Pipelining:** Clients may send multiple concatenated RESP commands in a single TCP read buffer. The server must process all commands sequentially in FIFO order and return all RESP replies in matching order without dropping or interleaving frames.
3. **Multi-Bulk Arrays vs. Inline Commands:**
   - Standard client libraries (`redis-py`, `redis-cli`) send commands formatted as RESP Multi-Bulk Arrays (e.g. `*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n`).
   - Telnet, netcat, and health checkers send plain text **Inline Commands** separated by whitespace and terminated by `\r\n` (e.g. `PING\r\n`, `PING hello\r\n`, `SET k v\r\n`). The decoder must support both formats seamlessly.
4. **Binary Safety:** Bulk strings must handle arbitrary byte sequences, including UTF-8 multi-byte characters, embedded `\r\n`, whitespace, and null bytes (`\x00`).
5. **Command Case-Insensitivity:** Command names are case-insensitive (`ping`, `PING`, `Ping`, `sEt`, `gEt` must all route to the same handler). Arguments/keys retain their exact case.

---

## 6. Supported Commands & Parity Semantics

| Command | Signature & Description | Success RESP Reply | Error RESP Reply |
| :--- | :--- | :--- | :--- |
| `PING` | `PING [message]`<br>Tests connection liveness. | 0 args: `+PONG\r\n`<br>1 arg: `$<len>\r\n<message>\r\n` | `>1` args: `-ERR wrong number of arguments for 'ping' command\r\n` |
| `ECHO` | `ECHO message`<br>Echoes the given string. | `$<len>\r\n<message>\r\n` | `!=1` arg: `-ERR wrong number of arguments for 'echo' command\r\n` |
| `QUIT` | `QUIT`<br>Asks the server to close the connection. | `+OK\r\n` (server closes TCP connection after reply) | `!=0` args: `-ERR wrong number of arguments for 'quit' command\r\n` |
| `SET` | `SET key value [EX seconds] [PX ms] [NX\|XX]`<br>Sets string value with optional expiration and existence flags. | `+OK\r\n` (if set)<br>`$-1\r\n` (if condition `NX` or `XX` not met) | `<2` args: `-ERR wrong number of arguments for 'set' command\r\n`<br>Both `NX` & `XX`: `-ERR syntax error\r\n`<br>Invalid TTL: `-ERR value is not an integer or out of range\r\n` |
| `GET` | `GET key`<br>Gets the string value of a key. | `$<len>\r\n<val>\r\n`<br>`$-1\r\n` (if key missing or expired) | `!=1` arg: `-ERR wrong number of arguments for 'get' command\r\n` |
| `DEL` | `DEL key [key ...]`<br>Removes specified key(s). | `:<count>\r\n` (integer count of keys removed) | `<1` arg: `-ERR wrong number of arguments for 'del' command\r\n` |
| `EXISTS` | `EXISTS key [key ...]`<br>Returns count of existing keys. | `:<count>\r\n` (sum of existing keys; duplicates counted) | `<1` arg: `-ERR wrong number of arguments for 'exists' command\r\n` |
| `INCR` | `INCR key`<br>Increments the integer value of a key by 1. | `:<new_int_value>\r\n` | `!=1` arg: `-ERR wrong number of arguments for 'incr' command\r\n`<br>Non-integer: `-ERR value is not an integer or out of range\r\n` |
| `DECR` | `DECR key`<br>Decrements the integer value of a key by 1. | `:<new_int_value>\r\n` | `!=1` arg: `-ERR wrong number of arguments for 'decr' command\r\n`<br>Non-integer: `-ERR value is not an integer or out of range\r\n` |
| `EXPIRE` | `EXPIRE key seconds`<br>Sets a timeout on key in seconds. | `:1\r\n` (timeout set)<br>`:0\r\n` (key missing or expired) | `!=2` args: `-ERR wrong number of arguments for 'expire' command\r\n`<br>Non-integer: `-ERR value is not an integer or out of range\r\n` |
| `TTL` | `TTL key`<br>Returns remaining TTL in seconds. | `:-2\r\n` (key missing/expired)<br>`:-1\r\n` (key exists, no expiry)<br>`:<seconds>\r\n` (remaining positive seconds) | `!=1` arg: `-ERR wrong number of arguments for 'ttl' command\r\n` |
| `KEYS` | `KEYS pattern`<br>Returns all keys matching glob pattern (`*`, `?`, `[abc]`, `\*`). | `*<count>\r\n$<len>\r\n<key1>\r\n...` (`*0\r\n` if no matches) | `!=1` arg: `-ERR wrong number of arguments for 'keys' command\r\n` |
| `FLUSHALL` | `FLUSHALL`<br>Deletes all keys and truncates AOF. | `+OK\r\n` | None |
| `COMMAND` | `COMMAND [DOCS]`<br>Driver capability discovery. | `*0\r\n` (or command list array) | None |
| `INFO` | `INFO [section]`<br>Driver handshake & stats. | `$0\r\n\r\n` (or server info string) | None |
| `CLIENT` | `CLIENT SETNAME\|GETNAME`<br>Driver handshake. | `+OK\r\n` | None |
| *Unknown* | Any unrecognized command `<NAME>` | None | `-ERR unknown command '<NAME>'\r\n` |

### 6.1 Special Semantics & Edge Cases
1. **`SET` Overwrite Behavior:** Overwriting a key with `SET key new_val` (without `EX`/`PX`) clears any existing expiration on that key, making it persistent (`TTL` becomes `-1`).
2. **`SET` Duration Bounds, Flag Order & PX Conversion:** `EX` requires positive integer seconds; `PX` requires positive integer milliseconds. If duration $\le 0$, return `-ERR value is not an integer or out of range\r\n`. Flag ordering must be flexible (e.g. `SET k v EX 10 NX` and `SET k v NX EX 10` are both valid). **Critical:** `PX <ms>` MUST be converted to an absolute expiration timestamp as `expire_at = clock() + ms / 1000.0` — store the absolute `float`, not the relative millisecond offset. This follows the same absolute-timestamp invariant as `EX`.
3. **`INCR`/`DECR` Initial Value & TTL:** If the key does not exist, it is initialized to `"0"` prior to modification (becoming `1` or `-1`). If the key already has an expiration, that expiration timestamp MUST be preserved after `INCR`/`DECR`.
4. **`EXPIRE` Non-Positive Durations:** If `EXPIRE key seconds` is called with `seconds <= 0`, the key MUST be deleted immediately. Returns `:1\r\n` if the key existed, `:0\r\n` otherwise.
5. **Connection Negotiation Commands:** Modern Redis drivers (`redis-py` v5+) automatically issue `COMMAND`, `INFO`, or `CLIENT SETNAME` on connection. Returning `*0\r\n` or `+OK\r\n` satisfies the handshake cleanly without erroring out.

---

## 7. Store Semantics & Expiration Engine

1. **Storage Structure:** In-memory dictionary mapping UTF-8 string keys to string values, paired with an expiration map tracking absolute expiration timestamps (Unix epoch seconds as `float`).
2. **Deterministic Time Injection:** The `Store` accepts a `Clock` callable (`Callable[[], float]`, default `time.time`) via dependency injection. All TTL calculations, expiration comparisons, and AOF timestamp creations MUST use this clock.
3. **Dual-Mode Expiration Strategy:**
   - **Lazy Eviction:** On any key access (`GET`, `SET`, `DEL`, `EXISTS`, `INCR`, `DECR`, `TTL`, `EXPIRE`), if current time $\ge$ expiration timestamp, the key is purged before completing the operation.
   - **Active Sweep:** Before executing `KEYS` or `FLUSHALL`, the store performs an active scan to evict all expired keys so stale keys never appear in query results.
4. **Concurrency Safety:** All store mutations and queries execute under a shared `asyncio.Lock` owned by the `Store` instance, guaranteeing serialized atomic operations across concurrent client connections. The AOF `log_mutation()` call MUST happen **inside** the acquired lock, before the lock is released and before the RESP reply is written to the client. This ensures no two commands can interleave their store change and AOF append.

---

## 8. Persistence Architecture (AOF Engine)

`pyedis` implements an Append-Only File (AOF) durability engine to ensure zero data loss across restarts.

### 8.1 AOF Record Schema
Every state-modifying mutation (`SET`, `DEL`, `INCR`, `DECR`, `EXPIRE`, `FLUSHALL`) appends exactly one JSON line to `<PYEDIS_DATA_DIR>/dump.aof`:
- `{"op":"SET","key":"<k>","value":"<v>","expire_at":<timestamp_float_or_null>}`
- `{"op":"DEL","key":"<k>"}`
- `{"op":"INCR","key":"<k>"}` / `{"op":"DECR","key":"<k>"}`
- `{"op":"EXPIRE","key":"<k>","expire_at":<timestamp_float>}`
- `{"op":"FLUSHALL"}`

> [!IMPORTANT]
> **Absolute Expiration Invariant:** Expirations stored in `dump.aof` MUST use absolute Unix epoch timestamps (`expire_at`), NOT relative durations. When replaying the AOF on startup, keys whose `expire_at` has already passed are immediately evicted and not revived with fresh lifetimes.

### 8.2 Fsync & Startup Replay
1. **Fsync Guarantee:** When `PYEDIS_AOF_FSYNC=true` (default), the server calls `os.fsync()` on the open file descriptor after writing each mutation before transmitting the RESP reply.
2. **Startup Replay:** On server initialization, if `dump.aof` exists in `PYEDIS_DATA_DIR`, lines are replayed sequentially into the store.
3. **Crash Recovery & Corrupt Trailing Line Tolerance:** If the server terminated abruptly (`SIGKILL`) during a write, the final line in `dump.aof` may be truncated. The replay engine MUST log `pyedis: ignoring corrupt trailing AOF line` and load all preceding valid lines.
4. **`FLUSHALL` Truncation:** Executing `FLUSHALL` immediately truncates `dump.aof` to 0 bytes on disk.

---

## 9. Phased Implementation & User Story Roadmap

To ensure high modularity and clean verification gates during autonomous Noctifab execution, the development roadmap decomposes into 5 sequential phases:

```
Phase 1: Toolchain, Packaging & RESP Framing Engine (src/resp.py, tests/unit/test_resp.py)
   │
   ▼
Phase 2: In-Memory Store & Clock DI Expiration Engine (src/store.py, tests/unit/test_store.py)
   │
   ▼
Phase 3: Command Router & Redis Parity Handlers (src/commands.py, tests/unit/test_commands.py)
   │
   ▼
Phase 4: AOF Durability & Startup Replay Engine (src/persistence.py, tests/unit/test_persistence.py)
   │
   ▼
Phase 5: Async TCP Server, Concurrency, Documentation & CI Integration Suite (src/main.py, tests/integration/test_server.py, tests/e2e/run_tests.sh, README.md, docs/, .readthedocs.yaml, .github/workflows/ci.yml)
```

- **Phase 5 Documentation & CI Mandate for Generators:**
  - Generators MUST implement the async TCP server and complete integration/E2E test suite.
  - Generators MUST author the complete, comprehensive documentation suite (`README.md`, `docs/index.md`, `docs/api.md`, `.readthedocs.yaml`) detailing installation, usage, use cases, supported operations reference, and the precise level of Redis compatibility.
  - Generators MUST verify that the GitHub Actions CI pipeline (`.github/workflows/ci.yml`) runs linting, unit/integration tests, and containerized E2E tests cleanly on every push.

---

## 10. Conformance & Verification Test Matrix

> [!IMPORTANT]
> **Standard Library `unittest` Conformance Requirement:**
> All test modules must subclass `unittest.TestCase` (or `unittest.IsolatedAsyncioTestCase`) and run via `python3 -m unittest discover -s tests -v`. Do NOT import or reference `pytest` anywhere.

### 10.1 Unit Tests (`tests/unit/`)
- **`test_resp.py` (`unittest.TestCase`):** Tests encoding and decoding of all RESP types, partial chunk reassembly, pipelined buffers, inline commands, and binary safety.
- **`test_store.py` (`unittest.TestCase`):** Tests set, get, del, incr, decr, ttl, active sweep, and lazy eviction using an injected mock clock.
- **`test_commands.py` (`unittest.TestCase`):** Tests arity checking, unknown commands, case-insensitivity, syntax errors, `NX`/`XX`, and `EX`/`PX`.
- **`test_persistence.py` (`unittest.TestCase`):** Tests AOF append, startup replay, absolute expiration replay, corrupted trailing line tolerance, and `FLUSHALL` truncation.

### 10.2 Integration Tests (`tests/integration/`)
- **`test_server.py` (`unittest.IsolatedAsyncioTestCase`):** Spins up a live `pyedis` TCP server on an ephemeral port.
  - Raw socket interactions.
  - Full official `redis-py` (v5+) command test suite.
  - `redis-py` pipeline execution (`pipe = r.pipeline(); ...; pipe.execute()`).
  - Concurrent load (50 concurrent async tasks hammering `INCR`).
  - Server restart durability verification.

### 10.3 Black-Box E2E Tests (`tests/e2e/`)
- **Containerized Dual-Service Architecture (`docker-compose.e2e.yml`):** The E2E test suite executes exclusively within isolated Docker containers. `docker-compose.e2e.yml` is composed of exactly two services:
  1. **The Service (`pyedis-server`):** Runs the asynchronous Python `pyedis` server.
  2. **The Test Runner (`test-runner-e2e`):** An Alpine-based container containing Python, Bash, and Redis tools (`redis-cli`) that waits for `pyedis-server` healthiness and executes `tests/e2e/run_tests.sh`.
- **Zero Host Package Requirement:** NO system packages (specifically `redis-cli`) are required to be installed on the host machine. All black-box CLI assertions run strictly inside the test runner container.
- **Parametrized Host & Port:** `tests/e2e/run_tests.sh` MUST parameterize target host and port via environment variables `REDIS_HOST` (default `127.0.0.1`) and `REDIS_PORT` (default `6379`), making it directly executable inside `test-runner-e2e` (`REDIS_HOST=pyedis-server`) as well as on any local setup with zero modification.

### 10.4 Coverage Gate
Total test coverage of `src/` must be $\ge 95\%$ lines (`coverage run -m unittest discover -s tests && coverage report`).

---

## 11. Documentation Requirements & Generator Mandate

Generators MUST write complete, production-grade documentation across `README.md` and the `docs/` folder (`docs/index.md`, `docs/api.md`, `.readthedocs.yaml`). Documentation must NOT contain placeholder text or empty stubs.

### 11.1 Installation & Setup Documentation
The documentation must detail:
- **System Requirements:** Python 3.10+ / 3.14+, Docker (for containerized E2E testing).
- **Installation Instructions:**
  - Standard `pip` installation: `pip install -e .` or `pip install -r requirements.txt`.
  - Development installation via Makefile: `make install`.
- **Server Execution:**
  - Running via CLI: `python3 -m src.main` or `make run`.
  - Configuration via environment variables (`PORT`, `PYEDIS_DATA_DIR`, `PYEDIS_AOF_FSYNC`).

### 11.2 Usage Guide & Client Connection Examples
The documentation must provide clear, copy-pasteable connection examples:
- **`redis-cli` (Official Redis CLI):**
  ```bash
  redis-cli -p 6379 PING
  redis-cli -p 6379 SET user:101 "Alice" EX 60
  redis-cli -p 6379 GET user:101
  redis-cli -p 6379 INCR counter
  redis-cli -p 6379 TTL user:101
  ```
- **`redis-py` (Python Client v5+):**
  ```python
  import redis

  r = redis.Redis(host="localhost", port=6379, decode_responses=True)
  r.set("greeting", "Hello from pyedis!", ex=30)
  print(r.get("greeting"))  # Output: Hello from pyedis!

  # Pipelining support
  pipe = r.pipeline()
  pipe.set("a", "1").incr("a").get("a")
  results = pipe.execute()
  ```
- **Raw Socket / Telnet / Inline Protocol:**
  Demonstrating connection via `nc localhost 6379` or `telnet localhost 6379` sending raw inline commands (`PING\r\n`, `SET k v\r\n`).

### 11.3 Use Cases of `pyedis`
The documentation must articulate the primary use cases and benefits of `pyedis`:
1. **Lightweight Embedded/Local Redis Replacement for Testing & Development:**
   - Run integration and functional test suites in CI/CD pipelines without provisioning or managing a heavy external Redis daemon, background system service, or Docker container.
2. **Fast Mocking & Integration Test Environments:**
   - Instant startup (<50ms), zero external C/Rust dependencies, deterministic time injection for TTL testing, and full process isolation.
3. **Pure-Python Redis-Compatible Microservices & Edge Apps:**
   - Embed an in-process, RESP2/RESP3-compliant cache or state store directly into Python applications.
4. **Educational RESP & Async Protocol Reference:**
   - A clean, modern, fully typed (`mypy --strict`) reference implementation illustrating zero-copy RESP streaming decoders, `asyncio.start_server`, and AOF persistence with absolute timestamp replay.

### 11.4 Supported Operations Reference
The documentation must include a comprehensive reference table of all supported Redis commands:
- **System & Connection Management:**
  - `PING [message]` — Connection health verification.
  - `ECHO message` — Message echoing.
  - `QUIT` — Connection termination.
- **Key-Value String Operations:**
  - `SET key value [EX seconds] [PX milliseconds] [NX|XX]` — String assignment with existence flags and expiration.
  - `GET key` — String retrieval.
  - `DEL key [key ...]` — Key deletion (single or multiple).
  - `EXISTS key [key ...]` — Key existence counting.
- **Numerical Operations:**
  - `INCR key` / `DECR key` — Atomic increment / decrement with TTL preservation.
- **Key Expiration & Inspection:**
  - `EXPIRE key seconds` — Setting relative expiration timeouts.
  - `TTL key` — Querying remaining time-to-live (`-2`, `-1`, or positive seconds).
  - `KEYS pattern` — Glob pattern key matching (`*`, `?`, `[abc]`).
  - `FLUSHALL` — State wiping and AOF truncation.
- **Driver Handshake & Protocol Negotiation:**
  - `COMMAND [DOCS]`, `INFO [section]`, `CLIENT SETNAME|GETNAME` — Transparent client driver compatibility.

### 11.5 Level of Compatibility with Redis
The documentation must explicitly explain the level of compatibility and architectural boundaries:
- **100% Wire Protocol Compatibility (RESP2 & RESP3):** Exact framing parity for Simple Strings (`+`), Errors (`-`), Integers (`:`), Bulk Strings (`$`), and Arrays (`*`), along with inline command parsing.
- **100% Client Library Compatibility:** Seamless interoperability with standard tools (`redis-cli`, `redis-py` v5+, `ioredis`, Go `go-redis`, etc.).
- **Deterministic Semantics Parity:** Identical command names (case-insensitive), error message envelopes (`-ERR ...`), return formats, arity checks, and expiration behavior.
- **Durability Model:** Append-Only File (`dump.aof`) with JSON-formatted records and absolute epoch timestamps (`expire_at`), guaranteeing durability without snapshotting overhead.
- **Architectural Scope & Deliberate Exclusions:**
  - *In Scope:* Core string operations, numerical operations, TTL expiration, active/lazy sweeps, AOF durability, TCP async server.
  - *Out of Scope (By Design for Lightweight Footprint):* Advanced compound data structures (Hashes, Sets, Sorted Sets, Streams, Bitmaps), Pub/Sub messaging, Lua scripting (`EVAL`), Redis Cluster / Sentinel replication, and binary RDB snapshotting.

### 11.6 Documentation Files & Structure
- **`README.md`**: Main repository guide featuring overview, quick start, installation, use cases, command table, compatibility matrix, and developer commands (`make test`, `make lint`, `make e2e`).
- **`docs/index.md`**: Entry point for Read the Docs covering architecture, key features, getting started, and design philosophy.
- **`docs/api.md`**: Detailed technical reference covering RESP specification, full command reference, AOF persistence mechanics, and Redis compatibility comparison.
- **`.readthedocs.yaml`**: Standard configuration file for Read the Docs builds.

---

## 12. Definition of Done (DoD)

To consider `pyedis` fully implemented, the project must satisfy:
1. **Public RESP API & CLI Compatibility:** Native Redis RESP2/RESP3 wire-protocol TCP server operating on port 6379, passing all command assertions via official `redis-cli` and `redis-py` (v5+).
2. **Persistence & Durability Invariant:** AOF persistence engine logs mutations with absolute `expire_at` timestamps, tolerates corrupt trailing lines, and successfully restores state on restart.
3. **Linting Invariant:** Zero findings under `ruff check src tests` AND `mypy --strict src`.
4. **Verification Criteria:** 100% test pass rate on `make test` (unit + integration executed via standard library `unittest`, ZERO `pytest` usage) and `make e2e` (containerized black-box test harness), with $\ge 95\%$ test coverage across `src/`.
5. **Comprehensive Documentation:** Complete `README.md`, `docs/index.md`, `docs/api.md`, and `.readthedocs.yaml` authored by generators with full installation instructions, usage examples, use cases, supported operations reference, and Redis compatibility level.
6. **GitHub Actions CI Pipeline:** `.github/workflows/ci.yml` runs on every push (and PR) across all branches, verifying that linters, unit/integration tests, and containerized E2E tests execute and pass cleanly.
