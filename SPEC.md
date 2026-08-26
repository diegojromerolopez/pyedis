# `pyedis` Specification: Native Redis RESP Key-Value Store in Python 3.14

## 1. Overview & Architectural Goals

`pyedis` is a high-performance, in-memory key-value store with a **native Redis wire-protocol (RESP2/RESP3) API exposed over TCP** (default port `6379`), written in modern Python (3.14 / 3.10+) with strict static typing (`mypy --strict src`) and standard library tooling. It implements the **full Redis command suite** across all core data types (Strings, Lists, Hashes, Sets, Sorted Sets, Streams, Bitmaps, Geospatial, Keys/Generic, Server, Connection, Transactions, Pub/Sub, and Scripting) with deterministic RESP reply and error envelopes, and persists state to an append-only file (AOF) using absolute expiration timestamps so data and TTLs survive process restarts and sudden terminations (`SIGKILL`). Standard Redis client utilities (`redis-cli`, `redis-py` v5+) MUST be 100% compatible with `pyedis`.

> [!IMPORTANT]
> **FULL REDIS COMMAND SUITE MANDATE: ALL COMMANDS MUST BE IMPLEMENTED**
> Every Redis command specified across all categories in this document MUST be fully implemented. The server must not return unknown command errors for any catalogued command.

`pyedis` exercises the Python ecosystem seams: async TCP socket streams (`asyncio.start_server`), zero-copy stream parsing, dependency injection (clock + store + AOF logger), absolute timestamp durability, and lock-protected async concurrency.

> [!IMPORTANT]
> **STRICT TESTING MANDATE: ZERO PYTEST USAGE & REAL DOCKER-COMPOSE E2E TESTS**
> - **`pytest` is STRICTLY FORBIDDEN:** The project MUST NOT use `pytest` under ANY circumstances.
> - **Zero `pytest` Dependencies or Artifacts:** Do NOT import `pytest`, do NOT list `pytest` in `requirements.txt` or `pyproject.toml`, do NOT create `conftest.py` or `pytest.ini`, and do NOT invoke `pytest` anywhere in Makefiles, scripts, or story contracts.
> - **Standard Library `unittest` Structure:** All unit and integration test classes MUST explicitly subclass `unittest.TestCase` (or `unittest.IsolatedAsyncioTestCase` for async test cases).
> - **Standard Library Mocking:** All test mocks MUST use `unittest.mock` (`MagicMock`, `AsyncMock`, `patch`).
> - **Standard Discovery Invocation:** All test suites MUST be executed via `python3 -m unittest discover -s tests -v` (wired to `make test`).
> - **REAL E2E Client-Server Feedback Loop (`docker-compose.e2e.yml`):** The project MUST provide REAL, multi-container End-to-End Client-Server tests defined in `docker-compose.e2e.yml`. A dedicated test runner service (`test-runner-e2e`) runs real client tests that connect over the network to the live `pyedis-server` service. These REAL E2E tests serve as essential, high-fidelity feedback for the correctness, stability, and protocol fidelity of the implementation.

### Key Architectural Invariants
1. **Native RESP2/RESP3 Protocol:** True binary-safe Redis serialization protocol framing supporting both multi-bulk arrays and whitespace-delimited inline commands.
2. **Zero External Framework Dependencies:** Pure standard library async TCP networking (`asyncio.start_server`). No FastAPI, Starlette, Uvicorn, or web frameworks.
3. **Deterministic Dependency Injection:** The in-memory store accepts an injected `Clock` callable (`Callable[[], float]`), allowing unit tests to freeze, step, and fast-forward time deterministically without `sleep()` delays.
4. **Absolute Expiration Durability:** AOF records store absolute Unix epoch timestamps (`expire_at`), ensuring expired keys are never resurrected across server reboots.
5. **Functional Focus for Intermediate Stories & Best-Effort Final Linting:** Intermediate feature user stories MUST be gated solely on functional correctness (`make test` and `make e2e`). All formatting (`ruff format`), linting (`ruff check`), and static type checking (`mypy --strict src`) MUST be deferred to a dedicated final user story ("Codebase Hardening, Formatting & Linting"). This final story operates on a **best-effort** basis: a 100% issue-free check is NOT mandatory; minor linter/typing warnings (e.g. 10%–20% of code lines with non-fatal issues or complex generic annotations) are permissible and MUST NOT block completion.
6. **REAL E2E Client-Server Validation:** Automated black-box validation in a multi-container Docker Compose harness (`docker-compose.e2e.yml`) providing continuous implementation feedback by testing real client connections against the server.
7. **500-Line Limit Rule:** No single Python source file (`.py`) may exceed 500 lines of code.

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
  3. **Lint & Static Type Verification:** Executes `make lint` (`ruff check src tests` and `mypy --strict src`) on a best-effort basis (non-blocking for intermediate development; finalized in the final hardening user story).
  4. **Unit & Integration Test Execution:** Executes `make test` (`python3 -m unittest discover -s tests -v`), verifying all unit and integration test suites pass with 100% success rate.
  5. **Containerized E2E Black-Box Test Execution:** Executes `make e2e` (`docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from test-runner-e2e`), ensuring the end-to-end black-box CLI test suite against the live containerized server succeeds completely.
- **Mandatory Pipeline Gate:** Unit/integration tests (`make test`) and containerized E2E black-box tests (`make e2e`) MUST all run and succeed with exit code 0 on every push for CI to pass. Linting and formatting are handled on a best-effort basis in the final hardening phase.

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

> [!IMPORTANT]
> **FULL REDIS COMMAND MANDATE: ALL COMMANDS LISTED BELOW MUST BE IMPLEMENTED**
> Every Redis command across all categories listed in this section MUST be fully implemented in `pyedis`. The server MUST NOT return `-ERR unknown command` for any of the catalogued commands. Full RESP2/RESP3 wire-protocol compatibility, parameter parsing, type validation, error envelopes, and parity semantics apply across all data types and server functions.

### 6.1 String Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `APPEND` | `APPEND key value`<br>Appends value to key string. Creates key if missing. | `:<new_string_length>\r\n` | `<2` args: `-ERR wrong number of arguments...`<br>Wrong Type: `-WRONGTYPE ...` | `APPEND msg " world"` &rarr; `:11\r\n` |
| `DECR` | `DECR key`<br>Decrements integer value of key by 1. | `:<new_int_value>\r\n` | Non-integer: `-ERR value is not an integer or out of range\r\n` | `DECR counter` &rarr; `:4\r\n` |
| `DECRBY` | `DECRBY key decrement`<br>Decrements key integer value by decrement amount. | `:<new_int_value>\r\n` | Non-integer: `-ERR value is not an integer or out of range\r\n` | `DECRBY counter 5` &rarr; `:-1\r\n` |
| `GET` | `GET key`<br>Returns string value of key. | `$<len>\r\n<val>\r\n`<br>`$-1\r\n` (if missing/expired) | Wrong Type: `-WRONGTYPE Operation against a key holding the wrong kind of value\r\n` | `GET user:1` &rarr; `$5\r\nAlice\r\n` |
| `GETDEL` | `GETDEL key`<br>Gets string value and atomically deletes the key. | `$<len>\r\n<val>\r\n`<br>`$-1\r\n` (if missing/expired) | Wrong Type: `-WRONGTYPE ...` | `GETDEL token` &rarr; `$4\r\nsecret\r\n` |
| `GETEX` | `GETEX key [EX s\|PX ms\|EXAT ts\|PXAT ms-ts\|PERSIST]`<br>Gets value and updates/clears TTL. | `$<len>\r\n<val>\r\n`<br>`$-1\r\n` (if missing/expired) | Syntax/Range errors | `GETEX session EX 300` &rarr; `$8\r\nactive_1\r\n` |
| `GETRANGE` | `GETRANGE key start end`<br>Returns substring from start to end (supports negative offsets). | `$<len>\r\n<substring>\r\n` | `!=3` args: `-ERR wrong number of arguments...` | `GETRANGE msg 0 4` &rarr; `$5\r\nHello\r\n` |
| `GETSET` | `GETSET key value`<br>Atomically sets string value and returns old value. | `$<len>\r\n<old_val>\r\n`<br>`$-1\r\n` (if missing) | `!=2` args: `-ERR wrong number of arguments...` | `GETSET count "10"` &rarr; `$1\r\n5\r\n` |
| `INCR` | `INCR key`<br>Increments key integer value by 1 (initializes to "0" if missing). | `:<new_int_value>\r\n` | Non-integer: `-ERR value is not an integer or out of range\r\n` | `INCR hits` &rarr; `:1\r\n` |
| `INCRBY` | `INCRBY key increment`<br>Increments key integer value by given integer increment. | `:<new_int_value>\r\n` | Non-integer: `-ERR value is not an integer or out of range\r\n` | `INCRBY score 10` &rarr; `:15\r\n` |
| `INCRBYFLOAT` | `INCRBYFLOAT key increment`<br>Increments key float value by given float increment. | `$<len>\r\n<new_float_str>\r\n` | Non-float: `-ERR value is not a valid float\r\n` | `INCRBYFLOAT temp 2.5` &rarr; `$4\r\n22.5\r\n` |
| `LCS` | `LCS key1 key2 [LEN] [IDX] [MINMATCHLEN len] [WITHMATCHLEN]`<br>Computes Longest Common Subsequence between two strings. | String: `$<len>\r\n<seq>\r\n`<br>LEN: `:<len>\r\n`<br>IDX: `*<matches>` | Key missing or wrong type errors | `LCS key1 key2` &rarr; `$4\r\nabcd\r\n`<br>`LCS key1 key2 LEN` &rarr; `:4\r\n` |
| `MGET` | `MGET key [key ...]`<br>Returns values of all specified keys in order. | `*<count>\r\n$<len>\r\n<v1>\r\n...` (with `$-1\r\n` for missing) | `<1` arg: `-ERR wrong number of arguments...` | `MGET k1 k2` &rarr; `*2\r\n$1\r\na\r\n$-1\r\n` |
| `MSET` | `MSET key value [key value ...]`<br>Sets multiple key-value pairs atomically. | `+OK\r\n` | Odd arguments: `-ERR wrong number of arguments...` | `MSET a "1" b "2"` &rarr; `+OK\r\n` |
| `MSETNX` | `MSETNX key value [key value ...]`<br>Sets multiple pairs only if NONE of the keys exist. | `:1\r\n` (all set)<br>`:0\r\n` (none set) | Odd arguments: `-ERR wrong number of arguments...` | `MSETNX a "1" c "3"` &rarr; `:0\r\n` |
| `PSETEX` | `PSETEX key milliseconds value`<br>Sets value with millisecond TTL. | `+OK\r\n` | Invalid TTL: `-ERR value is not an integer or out of range\r\n` | `PSETEX k 500 "val"` &rarr; `+OK\r\n` |
| `SET` | `SET key value [EX s\|PX ms\|EXAT ts\|PXAT ms-ts\|KEEPTTL] [NX\|XX] [GET]`<br>Sets string with options. | `+OK\r\n` (or old val if `GET`)<br>`$-1\r\n` (if condition failed) | `<2` args or both `NX` & `XX`: `-ERR syntax error\r\n` | `SET k v EX 60 NX` &rarr; `+OK\r\n` |
| `SETEX` | `SETEX key seconds value`<br>Sets value with second TTL. | `+OK\r\n` | Invalid TTL: `-ERR value is not an integer or out of range\r\n` | `SETEX k 10 "val"` &rarr; `+OK\r\n` |
| `SETNX` | `SETNX key value`<br>Sets value only if key does not exist. | `:1\r\n` (set)<br>`:0\r\n` (not set) | `!=2` args: `-ERR wrong number of arguments...` | `SETNX lock "held"` &rarr; `:1\r\n` |
| `SETRANGE` | `SETRANGE key offset value`<br>Overwrites part of string starting at offset. | `:<length_after_modification>\r\n` | `!=3` args: `-ERR wrong number of arguments...` | `SETRANGE k 6 "Redis"` &rarr; `:11\r\n` |
| `STRLEN` | `STRLEN key`<br>Returns length of string value. | `:<len>\r\n` (0 if missing) | `!=1` arg: `-ERR wrong number of arguments...` | `STRLEN k` &rarr; `:5\r\n` |
| `SUBSTR` | `SUBSTR key start end`<br>Alias for `GETRANGE`. | `$<len>\r\n<substring>\r\n` | `!=3` args: `-ERR wrong number of arguments...` | `SUBSTR k 0 2` &rarr; `$3\r\nHel\r\n` |

### 6.2 Bitmaps & Bitfield Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `SETBIT` | `SETBIT key offset value`<br>Sets or clears bit at offset (0 or 1). | `:0\r\n` or `:1\r\n` (original bit) | Offset out of range errors | `SETBIT bits 7 1` &rarr; `:0\r\n` |
| `GETBIT` | `GETBIT key offset`<br>Returns bit value at offset (0 or 1). | `:0\r\n` or `:1\r\n` | `!=2` args errors | `GETBIT bits 7` &rarr; `:1\r\n` |
| `BITCOUNT` | `BITCOUNT key [start end [BYTE\|BIT]]`<br>Counts set bits (population count) in string. | `:<count>\r\n` | Syntax/range errors | `BITCOUNT bits` &rarr; `:1\r\n` |
| `BITPOS` | `BITPOS key bit [start [end [BYTE\|BIT]]]`<br>Finds position of first bit set to 0 or 1. | `:<position>\r\n` (-1 if not found) | Syntax/range errors | `BITPOS bits 1` &rarr; `:7\r\n` |
| `BITOP` | `BITOP AND\|OR\|XOR\|NOT destkey srckey [srckey ...]`<br>Performs bitwise operations. | `:<dest_string_length>\r\n` | Syntax/arity errors | `BITOP AND dest k1 k2` &rarr; `:2\r\n` |
| `BITFIELD` | `BITFIELD key [GET type off] [SET type off val] [INCRBY type off inc] [OVERFLOW WRAP\|SAT\|FAIL]` | `*<results_array>\r\n` | Syntax/arity errors | `BITFIELD mykey GET u4 0` &rarr; `*1\r\n:5\r\n` |

### 6.3 List Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `LPUSH` | `LPUSH key element [element ...]`<br>Prepends elements to list head. | `:<len_after_push>\r\n` | Wrong Type: `-WRONGTYPE ...` | `LPUSH list a b` &rarr; `:2\r\n` |
| `RPUSH` | `RPUSH key element [element ...]`<br>Appends elements to list tail. | `:<len_after_push>\r\n` | Wrong Type: `-WRONGTYPE ...` | `RPUSH list c` &rarr; `:3\r\n` |
| `LPUSHX` | `LPUSHX key element [element ...]`<br>Prepends elements only if list exists. | `:<len_after_push>\r\n` (0 if missing) | `<2` args errors | `LPUSHX list z` &rarr; `:4\r\n` |
| `RPUSHX` | `RPUSHX key element [element ...]`<br>Appends elements only if list exists. | `:<len_after_push>\r\n` (0 if missing) | `<2` args errors | `RPUSHX missing x` &rarr; `:0\r\n` |
| `LPOP` | `LPOP key [count]`<br>Removes and returns first element(s) from list. | `$<len>\r\n<elem>\r\n` or `*<count>` (or `$-1\r\n`) | `<1` arg errors | `LPOP list` &rarr; `$1\r\nb\r\n` |
| `RPOP` | `RPOP key [count]`<br>Removes and returns last element(s) from list. | `$<len>\r\n<elem>\r\n` or `*<count>` (or `$-1\r\n`) | `<1` arg errors | `RPOP list` &rarr; `$1\r\nc\r\n` |
| `LRANGE` | `LRANGE key start stop`<br>Returns range of elements from list. | `*<count>\r\n$<len>\r\n<elem1>...` | `!=3` args errors | `LRANGE list 0 -1` &rarr; `*2\r\n$1\r\nb\r\n$1\r\na\r\n` |
| `LLEN` | `LLEN key`<br>Returns length of list. | `:<length>\r\n` (0 if missing) | `!=1` arg errors | `LLEN list` &rarr; `:2\r\n` |
| `LINDEX` | `LINDEX key index`<br>Returns element at index (zero-based). | `$<len>\r\n<elem>\r\n` or `$-1\r\n` | `!=2` args errors | `LINDEX list 0` &rarr; `$1\r\nb\r\n` |
| `LSET` | `LSET key index element`<br>Sets list element at index. | `+OK\r\n` | Index out of range errors | `LSET list 0 "new"` &rarr; `+OK\r\n` |
| `LINSERT` | `LINSERT key BEFORE\|AFTER pivot element`<br>Inserts element relative to pivot. | `:<new_len>\r\n` (-1 if no pivot) | Syntax/arity errors | `LINSERT list BEFORE a x` &rarr; `:3\r\n` |
| `LREM` | `LREM key count element`<br>Removes count occurrences of element. | `:<count_removed>\r\n` | `!=3` args errors | `LREM list 1 a` &rarr; `:1\r\n` |
| `LTRIM` | `LTRIM key start stop`<br>Trims list to specified range. | `+OK\r\n` | `!=3` args errors | `LTRIM list 0 1` &rarr; `+OK\r\n` |
| `LMOVE` | `LMOVE source destination LEFT\|RIGHT LEFT\|RIGHT`<br>Moves element between lists. | `$<len>\r\n<elem>\r\n` or `$-1\r\n` | Syntax/arity errors | `LMOVE src dst RIGHT LEFT` &rarr; `$1\r\nx\r\n` |
| `LPOS` | `LPOS key element [RANK rank] [COUNT num] [MAXLEN len]`<br>Returns matching index/indices. | `:<index>\r\n` or `*<indices>\r\n` or `$-1\r\n` | Syntax/arity errors | `LPOS list a` &rarr; `:0\r\n` |
| `RPOPLPUSH` | `RPOPLPUSH source destination`<br>Atomically moves last element to destination head. | `$<len>\r\n<elem>\r\n` or `$-1\r\n` | `!=2` args errors | `RPOPLPUSH q1 q2` &rarr; `$3\r\njob\r\n` |
| `BLPOP` | `BLPOP key [key ...] timeout`<br>Blocking pop from head of first non-empty list. | `*2\r\n$<len>\r\n<key>\r\n$<len>\r\n<val>\r\n` or `*-1\r\n` | `<2` args errors | `BLPOP q 1` &rarr; `*2\r\n$1\r\nq\r\n$1\r\na\r\n` |
| `BRPOP` | `BRPOP key [key ...] timeout`<br>Blocking pop from tail of first non-empty list. | `*2\r\n$<len>\r\n<key>\r\n$<len>\r\n<val>\r\n` or `*-1\r\n` | `<2` args errors | `BRPOP q 1` &rarr; `*2\r\n$1\r\nq\r\n$1\r\nb\r\n` |
| `BLMOVE` | `BLMOVE source destination LEFT\|RIGHT LEFT\|RIGHT timeout`<br>Blocking atomic move between lists. | `$<len>\r\n<elem>\r\n` or `$-1\r\n` | Syntax/arity errors | `BLMOVE s d RIGHT LEFT 2` &rarr; `$1\r\na\r\n` |
| `BRPOPLPUSH` | `BRPOPLPUSH source destination timeout`<br>Blocking atomic return and push. | `$<len>\r\n<elem>\r\n` or `$-1\r\n` | Syntax/arity errors | `BRPOPLPUSH s d 2` &rarr; `$1\r\na\r\n` |

### 6.4 Hash Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `HSET` | `HSET key field value [field value ...]`<br>Sets field-value pairs in hash. | `:<count_new_fields_added>\r\n` | Odd arguments errors | `HSET user name "Ada" age "30"` &rarr; `:2\r\n` |
| `HGET` | `HGET key field`<br>Returns value of hash field. | `$<len>\r\n<val>\r\n` or `$-1\r\n` | `!=2` args errors | `HGET user name` &rarr; `$3\r\nAda\r\n` |
| `HMSET` | `HMSET key field value [field value ...]`<br>Sets multiple hash fields (alias for HSET). | `+OK\r\n` | Odd arguments errors | `HMSET user k1 v1` &rarr; `+OK\r\n` |
| `HMGET` | `HMGET key field [field ...]`<br>Returns values for specified fields. | `*<count>\r\n$<len>\r\n<v1>\r\n...` | `<2` args errors | `HMGET user name age missing` &rarr; `*3\r\n$3\r\nAda\r\n$2\r\n30\r\n$-1\r\n` |
| `HGETALL` | `HGETALL key`<br>Returns all fields and values in hash. | `*<2*count>\r\n$<len>\r\n<f1>\r\n$<len>\r\n<v1>...` | `!=1` arg errors | `HGETALL user` &rarr; `*4\r\n$4\r\nname\r\n$3\r\nAda\r\n$3\r\nage\r\n$2\r\n30\r\n` |
| `HDEL` | `HDEL key field [field ...]`<br>Deletes one or more hash fields. | `:<count_fields_removed>\r\n` | `<2` args errors | `HDEL user age` &rarr; `:1\r\n` |
| `HEXISTS` | `HEXISTS key field`<br>Determines if a hash field exists. | `:1\r\n` (exists)<br>`:0\r\n` (missing) | `!=2` args errors | `HEXISTS user name` &rarr; `:1\r\n` |
| `HKEYS` | `HKEYS key`<br>Returns all field names in hash. | `*<count>\r\n$<len>\r\n<f1>...` | `!=1` arg errors | `HKEYS user` &rarr; `*1\r\n$4\r\nname\r\n` |
| `HVALS` | `HVALS key`<br>Returns all values in hash. | `*<count>\r\n$<len>\r\n<v1>...` | `!=1` arg errors | `HVALS user` &rarr; `*1\r\n$3\r\nAda\r\n` |
| `HLEN` | `HLEN key`<br>Returns number of fields contained in hash. | `:<number_of_fields>\r\n` | `!=1` arg errors | `HLEN user` &rarr; `:1\r\n` |
| `HINCRBY` | `HINCRBY key field increment`<br>Increments integer value of hash field. | `:<new_int_value>\r\n` | Non-integer errors | `HINCRBY user visits 1` &rarr; `:1\r\n` |
| `HINCRBYFLOAT` | `HINCRBYFLOAT key field increment`<br>Increments float value of hash field. | `$<len>\r\n<new_float_str>\r\n` | Non-float errors | `HINCRBYFLOAT user rate 0.5` &rarr; `$3\r\n1.5\r\n` |
| `HSETNX` | `HSETNX key field value`<br>Sets field value only if field does not exist. | `:1\r\n` (set)<br>`:0\r\n` (not set) | `!=3` args errors | `HSETNX user email "a@b.c"` &rarr; `:1\r\n` |
| `HRANDFIELD` | `HRANDFIELD key [count [WITHVALUES]]`<br>Returns random field(s) from hash. | `$<len>\r\n<field>\r\n` or `*<fields_or_pairs>\r\n` | Syntax/arity errors | `HRANDFIELD user 1` &rarr; `*1\r\n$4\r\nname\r\n` |
| `HSCAN` | `HSCAN key cursor [MATCH pattern] [COUNT count]`<br>Incrementally iterates hash fields and values. | `*2\r\n$<len>\r\n<next_cursor>\r\n*<field_val_array>\r\n` | Syntax/arity errors | `HSCAN user 0` &rarr; `*2\r\n$1\r\n0\r\n*2\r\n$4\r\nname\r\n$3\r\nAda\r\n` |
| `HSTRLEN` | `HSTRLEN key field`<br>Returns length of value string associated with field. | `:<len>\r\n` (0 if missing) | `!=2` args errors | `HSTRLEN user name` &rarr; `:3\r\n` |

### 6.5 Set Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `SADD` | `SADD key member [member ...]`<br>Adds members to set. | `:<count_new_members_added>\r\n` | `<2` args errors | `SADD tags db nosql` &rarr; `:2\r\n` |
| `SREM` | `SREM key member [member ...]`<br>Removes members from set. | `:<count_members_removed>\r\n` | `<2` args errors | `SREM tags nosql` &rarr; `:1\r\n` |
| `SMEMBERS` | `SMEMBERS key`<br>Returns all members of set. | `*<count>\r\n$<len>\r\n<m1>...` | `!=1` arg errors | `SMEMBERS tags` &rarr; `*1\r\n$2\r\ndb\r\n` |
| `SISMEMBER` | `SISMEMBER key member`<br>Tests if member is in set. | `:1\r\n` (member)<br>`:0\r\n` (not) | `!=2` args errors | `SISMEMBER tags db` &rarr; `:1\r\n` |
| `SMISMEMBER` | `SMISMEMBER key member [member ...]`<br>Tests multiple members for membership in set. | `*<count>\r\n:1\r\n:0\r\n...` | `<2` args errors | `SMISMEMBER tags db missing` &rarr; `*2\r\n:1\r\n:0\r\n` |
| `SCARD` | `SCARD key`<br>Returns set cardinality (number of members). | `:<count>\r\n` (0 if missing) | `!=1` arg errors | `SCARD tags` &rarr; `:1\r\n` |
| `SUNION` | `SUNION key [key ...]`<br>Returns union of all given sets. | `*<count>\r\n$<len>\r\n<m1>...` | `<1` arg errors | `SUNION s1 s2` &rarr; `*3\r\n$1\r\na\r\n$1\r\nb\r\n$1\r\nc\r\n` |
| `SUNIONSTORE` | `SUNIONSTORE destination key [key ...]`<br>Stores union of sets into destination key. | `:<cardinality_of_dest>\r\n` | `<2` args errors | `SUNIONSTORE s3 s1 s2` &rarr; `:3\r\n` |
| `SINTER` | `SINTER key [key ...]`<br>Returns intersection of given sets. | `*<count>\r\n$<len>\r\n<m1>...` | `<1` arg errors | `SINTER s1 s2` &rarr; `*1\r\n$1\r\nb\r\n` |
| `SINTERSTORE` | `SINTERSTORE destination key [key ...]`<br>Stores intersection into destination. | `:<cardinality_of_dest>\r\n` | `<2` args errors | `SINTERSTORE dest s1 s2` &rarr; `:1\r\n` |
| `SINTERCARD` | `SINTERCARD numkeys key [key ...] [LIMIT limit]`<br>Returns cardinality of intersection. | `:<count>\r\n` | Syntax/arity errors | `SINTERCARD 2 s1 s2` &rarr; `:1\r\n` |
| `SDIFF` | `SDIFF key [key ...]`<br>Returns difference between first set and other sets. | `*<count>\r\n$<len>\r\n<m1>...` | `<1` arg errors | `SDIFF s1 s2` &rarr; `*1\r\n$1\r\na\r\n` |
| `SDIFFSTORE` | `SDIFFSTORE destination key [key ...]`<br>Stores difference into destination. | `:<cardinality_of_dest>\r\n` | `<2` args errors | `SDIFFSTORE dest s1 s2` &rarr; `:1\r\n` |
| `SRANDMEMBER` | `SRANDMEMBER key [count]`<br>Returns random member(s) from set. | `$<len>\r\n<elem>\r\n` or `*<elems>\r\n` | Syntax/arity errors | `SRANDMEMBER tags` &rarr; `$2\r\ndb\r\n` |
| `SPOP` | `SPOP key [count]`<br>Removes and returns random member(s) from set. | `$<len>\r\n<elem>\r\n` or `*<elems>\r\n` | Syntax/arity errors | `SPOP tags` &rarr; `$2\r\ndb\r\n` |
| `SMOVE` | `SMOVE source destination member`<br>Moves member from source to destination. | `:1\r\n` (moved)<br>`:0\r\n` (not found) | `!=3` args errors | `SMOVE s1 s2 a` &rarr; `:1\r\n` |
| `SSCAN` | `SSCAN key cursor [MATCH pattern] [COUNT count]`<br>Incrementally iterates set elements. | `*2\r\n$<len>\r\n<next_cursor>\r\n*<elements>\r\n` | Syntax/arity errors | `SSCAN tags 0` &rarr; `*2\r\n$1\r\n0\r\n*1\r\n$2\r\ndb\r\n` |

### 6.6 Sorted Set (ZSet) Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `ZADD` | `ZADD key [NX\|XX] [GT\|LT] [CH] [INCR] score member [score member ...]`<br>Adds/updates scored members. | `:<count_added_or_changed>\r\n` (or float bulk if INCR) | Syntax/type errors | `ZADD lb 100 "alice" 90 "bob"` &rarr; `:2\r\n` |
| `ZCARD` | `ZCARD key`<br>Returns sorted set cardinality. | `:<count>\r\n` (0 if missing) | `!=1` arg errors | `ZCARD lb` &rarr; `:2\r\n` |
| `ZCOUNT` | `ZCOUNT key min max`<br>Counts members with scores in [min, max] range. | `:<count>\r\n` | `!=3` args errors | `ZCOUNT lb 90 100` &rarr; `:2\r\n` |
| `ZDIFF` | `ZDIFF numkeys key [key ...] [WITHSCORES]`<br>Computes difference of sorted sets. | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZDIFF 2 z1 z2` &rarr; `*1\r\n$1\r\na\r\n` |
| `ZDIFFSTORE` | `ZDIFFSTORE destination numkeys key [key ...]`<br>Stores difference into destination. | `:<cardinality_of_dest>\r\n` | Syntax/arity errors | `ZDIFFSTORE out 2 z1 z2` &rarr; `:1\r\n` |
| `ZINCRBY` | `ZINCRBY key increment member`<br>Increments score of member in sorted set. | `$<len>\r\n<new_score_str>\r\n` | Non-float score errors | `ZINCRBY lb 10 "bob"` &rarr; `$3\r\n100\r\n` |
| `ZINTER` | `ZINTER numkeys key [key ...] [WEIGHTS w ...] [AGGREGATE SUM\|MIN\|MAX] [WITHSCORES]` | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZINTER 2 z1 z2` &rarr; `*1\r\n$1\r\nb\r\n` |
| `ZINTERCARD` | `ZINTERCARD numkeys key [key ...] [LIMIT limit]`<br>Returns cardinality of intersection. | `:<count>\r\n` | Syntax/arity errors | `ZINTERCARD 2 z1 z2` &rarr; `:1\r\n` |
| `ZINTERSTORE` | `ZINTERSTORE destination numkeys key [key ...] [WEIGHTS w ...] [AGGREGATE SUM\|MIN\|MAX]` | `:<cardinality_of_dest>\r\n` | Syntax/arity errors | `ZINTERSTORE out 2 z1 z2` &rarr; `:1\r\n` |
| `ZLEXCOUNT` | `ZLEXCOUNT key min max`<br>Counts members between lexicographical bounds. | `:<count>\r\n` | Syntax/arity errors | `ZLEXCOUNT z [a [z` &rarr; `:2\r\n` |
| `ZMSCORE` | `ZMSCORE key member [member ...]`<br>Returns scores for specified members. | `*<count>\r\n$<len>\r\n<score>\r\n...` | `<2` args errors | `ZMSCORE lb alice missing` &rarr; `*2\r\n$3\r\n100\r\n$-1\r\n` |
| `ZPOPMAX` | `ZPOPMAX key [count]`<br>Removes and returns members with highest scores. | `*<2*count>\r\n$<len>\r\n<m>\r\n$<len>\r\n<s>...` | Syntax/arity errors | `ZPOPMAX lb 1` &rarr; `*2\r\n$5\r\nalice\r\n$3\r\n100\r\n` |
| `ZPOPMIN` | `ZPOPMIN key [count]`<br>Removes and returns members with lowest scores. | `*<2*count>\r\n$<len>\r\n<m>\r\n$<len>\r\n<s>...` | Syntax/arity errors | `ZPOPMIN lb 1` &rarr; `*2\r\n$3\r\nbob\r\n$2\r\n90\r\n` |
| `ZRANDMEMBER` | `ZRANDMEMBER key [count [WITHSCORES]]`<br>Returns random member(s) from sorted set. | `$<len>\r\n<m>\r\n` or `*<members>\r\n` | Syntax/arity errors | `ZRANDMEMBER lb` &rarr; `$5\r\nalice\r\n` |
| `ZRANGE` | `ZRANGE key min max [BYSCORE\|BYLEX] [REV] [LIMIT off count] [WITHSCORES]` | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZRANGE lb 0 -1 WITHSCORES` &rarr; `*4\r\n$3\r\nbob\r\n$2\r\n90\r\n$5\r\nalice\r\n$3\r\n100\r\n` |
| `ZRANGEBYSCORE` | `ZRANGEBYSCORE key min max [WITHSCORES] [LIMIT offset count]`<br>Queries members by score range. | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZRANGEBYSCORE lb 90 100` &rarr; `*2\r\n$3\r\nbob\r\n$5\r\nalice\r\n` |
| `ZRANGEBYLEX` | `ZRANGEBYLEX key min max [LIMIT offset count]`<br>Queries members by lexicographical range. | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZRANGEBYLEX z [a [z` &rarr; `*2\r\n$1\r\na\r\n$1\r\nb\r\n` |
| `ZRANGESTORE` | `ZRANGESTORE dst src min max [BYSCORE\|BYLEX] [REV] [LIMIT offset count]` | `:<cardinality_stored>\r\n` | Syntax/arity errors | `ZRANGESTORE out lb 0 1` &rarr; `:2\r\n` |
| `ZRANK` | `ZRANK key member [WITHSCORE]`<br>Returns 0-based rank from lowest to highest score. | `:<rank>\r\n` (or `$-1\r\n`) | `!=2` and `!=3` args errors | `ZRANK lb bob` &rarr; `:0\r\n` |
| `ZREM` | `ZREM key member [member ...]`<br>Removes members from sorted set. | `:<count_removed>\r\n` | `<2` args errors | `ZREM lb bob` &rarr; `:1\r\n` |
| `ZREMRANGEBYLEX` | `ZREMRANGEBYLEX key min max`<br>Removes members in lexicographical range. | `:<count_removed>\r\n` | `!=3` args errors | `ZREMRANGEBYLEX z [a [c` &rarr; `:2\r\n` |
| `ZREMRANGEBYRANK` | `ZREMRANGEBYRANK key start stop`<br>Removes members within rank range. | `:<count_removed>\r\n` | `!=3` args errors | `ZREMRANGEBYRANK lb 0 0` &rarr; `:1\r\n` |
| `ZREMRANGEBYSCORE` | `ZREMRANGEBYSCORE key min max`<br>Removes members within score range. | `:<count_removed>\r\n` | `!=3` args errors | `ZREMRANGEBYSCORE lb 0 50` &rarr; `:0\r\n` |
| `ZREVRANGE` | `ZREVRANGE key start stop [WITHSCORES]`<br>Returns members highest to lowest score. | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZREVRANGE lb 0 -1` &rarr; `*2\r\n$5\r\nalice\r\n$3\r\nbob\r\n` |
| `ZREVRANGEBYLEX` | `ZREVRANGEBYLEX key max min [LIMIT offset count]`<br>Reverse lexicographical query. | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZREVRANGEBYLEX z [z [a` &rarr; `*2\r\n$1\r\nb\r\n$1\r\na\r\n` |
| `ZREVRANGEBYSCORE` | `ZREVRANGEBYSCORE key max min [WITHSCORES] [LIMIT offset count]`<br>Reverse score query. | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZREVRANGEBYSCORE lb 100 90` &rarr; `*2\r\n$5\r\nalice\r\n$3\r\nbob\r\n` |
| `ZREVRANK` | `ZREVRANK key member [WITHSCORE]`<br>Returns rank from highest to lowest score. | `:<rank>\r\n` (or `$-1\r\n`) | Syntax/arity errors | `ZREVRANK lb alice` &rarr; `:0\r\n` |
| `ZSCAN` | `ZSCAN key cursor [MATCH pattern] [COUNT count]`<br>Incrementally iterates sorted set elements. | `*2\r\n$<len>\r\n<next_cursor>\r\n*<elem_scores>\r\n` | Syntax/arity errors | `ZSCAN lb 0` &rarr; `*2\r\n$1\r\n0\r\n*4\r\n$3\r\nbob\r\n$2\r\n90\r\n$5\r\nalice\r\n$3\r\n100\r\n` |
| `ZSCORE` | `ZSCORE key member`<br>Returns score of member. | `$<len>\r\n<score_str>\r\n` or `$-1\r\n` | `!=2` args errors | `ZSCORE lb alice` &rarr; `$3\r\n100\r\n` |
| `ZUNION` | `ZUNION numkeys key [key ...] [WEIGHTS w ...] [AGGREGATE SUM\|MIN\|MAX] [WITHSCORES]` | `*<count>\r\n$<len>\r\n<m1>...` | Syntax/arity errors | `ZUNION 2 z1 z2` &rarr; `*3\r\n$1\r\na\r\n$1\r\nb\r\n$1\r\nc\r\n` |
| `ZUNIONSTORE` | `ZUNIONSTORE destination numkeys key [key ...] [WEIGHTS w ...] [AGGREGATE SUM\|MIN\|MAX]` | `:<cardinality_of_dest>\r\n` | Syntax/arity errors | `ZUNIONSTORE out 2 z1 z2` &rarr; `:3\r\n` |
| `BZPOPMIN` | `BZPOPMIN key [key ...] timeout`<br>Blocking pop member with lowest score. | `*3\r\n$<len>\r\n<k>\r\n$<len>\r\n<m>\r\n$<len>\r\n<s>\r\n` or `*-1\r\n` | Arity/timeout errors | `BZPOPMIN lb 1` &rarr; `*3\r\n$2\r\nlb\r\n$3\r\nbob\r\n$2\r\n90\r\n` |
| `BZPOPMAX` | `BZPOPMAX key [key ...] timeout`<br>Blocking pop member with highest score. | `*3\r\n$<len>\r\n<k>\r\n$<len>\r\n<m>\r\n$<len>\r\n<s>\r\n` or `*-1\r\n` | Arity/timeout errors | `BZPOPMAX lb 1` &rarr; `*3\r\n$2\r\nlb\r\n$5\r\nalice\r\n$3\r\n100\r\n` |

### 6.7 Geospatial Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `GEOADD` | `GEOADD key [NX\|XX] [CH] lon lat member [lon lat member ...]`<br>Adds geospatial coordinates. | `:<count_added>\r\n` | Coordinate errors | `GEOADD cities 13.361389 38.115556 "Palermo"` &rarr; `:1\r\n` |
| `GEODIST` | `GEODIST key member1 member2 [M\|KM\|FT\|MI]`<br>Returns distance between two members. | `$<len>\r\n<dist_str>\r\n` (or `$-1\r\n`) | Unit errors | `GEODIST cities Palermo Catania KM` &rarr; `$7\r\n166.2742\r\n` |
| `GEOHASH` | `GEOHASH key member [member ...]`<br>Returns Geohash string representations. | `*<count>\r\n$<len>\r\n<hash>...` | Arity errors | `GEOHASH cities Palermo` &rarr; `*1\r\n$11\r\nsqc8b49rny0\r\n` |
| `GEOPOS` | `GEOPOS key member [member ...]`<br>Returns longitude and latitude of members. | `*<count>\r\n*2\r\n$<len>\r\n<lon>\r\n$<len>\r\n<lat>...` | Arity errors | `GEOPOS cities Palermo` &rarr; `*1\r\n*2\r\n$9\r\n13.361389\r\n$9\r\n38.115556\r\n` |
| `GEORADIUS` | `GEORADIUS key lon lat radius M\|KM\|FT\|MI [WITHCOORD] [WITHDIST] [WITHHASH] [COUNT c] [ASC\|DESC]` | `*<results_array>\r\n` | Syntax/coordinate errors | `GEORADIUS cities 15 37 200 KM` &rarr; `*2\r\n$7\r\nPalermo\r\n$7\r\nCatania\r\n` |
| `GEORADIUSBYMEMBER` | `GEORADIUSBYMEMBER key member radius M\|KM\|FT\|MI [WITHCOORD] [WITHDIST] [WITHHASH] [COUNT c]` | `*<results_array>\r\n` | Syntax/member errors | `GEORADIUSBYMEMBER cities Palermo 200 KM` &rarr; `*2\r\n$7\r\nPalermo\r\n$7\r\nCatania\r\n` |
| `GEOSEARCH` | `GEOSEARCH key [FROMMEMBER m\|FROMLONLAT lon lat] [BYRADIUS r unit\|BYBOX w h unit] [ASC\|DESC]` | `*<results_array>\r\n` | Syntax/coordinate errors | `GEOSEARCH cities FROMLONLAT 15 37 BYRADIUS 200 KM` &rarr; `*2\r\n$7\r\nPalermo\r\n$7\r\nCatania\r\n` |
| `GEOSEARCHSTORE` | `GEOSEARCHSTORE dst src [FROMMEMBER m\|FROMLONLAT lon lat] [BYRADIUS r unit\|BYBOX w h unit] [STOREDIST]` | `:<count_stored>\r\n` | Syntax/coordinate errors | `GEOSEARCHSTORE out cities FROMLONLAT 15 37 BYRADIUS 200 KM` &rarr; `:2\r\n` |

### 6.8 Generic & Key Management Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `COPY` | `COPY source destination [DB destination-db] [REPLACE]`<br>Copies value from source to destination. | `:1\r\n` (copied)<br>`:0\r\n` (not copied) | Syntax/arity errors | `COPY k1 k2 REPLACE` &rarr; `:1\r\n` |
| `DEL` | `DEL key [key ...]`<br>Removes specified key(s). | `:<count_removed>\r\n` | `<1` arg errors | `DEL k1 k2` &rarr; `:2\r\n` |
| `DUMP` | `DUMP key`<br>Returns serialized value stored at key. | `$<len>\r\n<bytes>\r\n` or `$-1\r\n` | `!=1` arg errors | `DUMP k` &rarr; `$10\r\n\x00\xc0\n\t...` |
| `EXISTS` | `EXISTS key [key ...]`<br>Returns count of existing keys. | `:<count_existing>\r\n` | `<1` arg errors | `EXISTS k1 k2` &rarr; `:1\r\n` |
| `EXPIRE` | `EXPIRE key seconds [NX\|XX\|GT\|LT]`<br>Sets expiration timeout in seconds. | `:1\r\n` (set)<br>`:0\r\n` (not set) | Invalid integer errors | `EXPIRE k 60` &rarr; `:1\r\n` |
| `EXPIREAT` | `EXPIREAT key unix-time-seconds [NX\|XX\|GT\|LT]`<br>Sets expiration at absolute Unix timestamp. | `:1\r\n` (set)<br>`:0\r\n` (not set) | Invalid timestamp errors | `EXPIREAT k 1893456000` &rarr; `:1\r\n` |
| `EXPIRETIME` | `EXPIRETIME key`<br>Returns absolute Unix expiration timestamp in seconds. | `:<timestamp>\r\n` (-1 no TTL, -2 missing) | `!=1` arg errors | `EXPIRETIME k` &rarr; `:1893456000\r\n` |
| `KEYS` | `KEYS pattern`<br>Returns all keys matching glob pattern (`*`, `?`, `[abc]`, `\*`). | `*<count>\r\n$<len>\r\n<k1>...` | `!=1` arg errors | `KEYS user:*` &rarr; `*1\r\n$6\r\nuser:1\r\n` |
| `MIGRATE` | `MIGRATE host port key\|"" dest-db timeout [COPY] [REPLACE] [AUTH pwd] [KEYS k ...]` | `+OK\r\n` or `+NOKEY\r\n` | Connection/syntax errors | `MIGRATE 127.0.0.1 6380 k 0 5000 COPY` &rarr; `+OK\r\n` |
| `MOVE` | `MOVE key db`<br>Moves key to another database index. | `:1\r\n` (moved)<br>`:0\r\n` (not moved) | `!=2` args errors | `MOVE k 1` &rarr; `:1\r\n` |
| `OBJECT` | `OBJECT ENCODING\|FREQ\|HELP\|IDLETIME\|REFCOUNT key`<br>Inspects object internals. | `$<len>\r\n<encoding>\r\n` or `:<int>\r\n` | Syntax errors | `OBJECT ENCODING k` &rarr; `$3\r\nraw\r\n` |
| `PERSIST` | `PERSIST key`<br>Removes existing timeout on key, making it persistent. | `:1\r\n` (cleared)<br>`:0\r\n` (no TTL/missing) | `!=1` arg errors | `PERSIST k` &rarr; `:1\r\n` |
| `PEXPIRE` | `PEXPIRE key milliseconds [NX\|XX\|GT\|LT]`<br>Sets expiration in milliseconds. | `:1\r\n` (set)<br>`:0\r\n` (not set) | Invalid integer errors | `PEXPIRE k 5000` &rarr; `:1\r\n` |
| `PEXPIREAT` | `PEXPIREAT key unix-time-milliseconds [NX\|XX\|GT\|LT]`<br>Sets expiration timestamp in ms. | `:1\r\n` (set)<br>`:0\r\n` (not set) | Invalid integer errors | `PEXPIREAT k 1893456000000` &rarr; `:1\r\n` |
| `PEXPIRETIME` | `PEXPIRETIME key`<br>Returns absolute Unix expiration timestamp in milliseconds. | `:<ms_timestamp>\r\n` (-1 no TTL, -2 missing) | `!=1` arg errors | `PEXPIRETIME k` &rarr; `:1893456000000\r\n` |
| `PTTL` | `PTTL key`<br>Returns remaining TTL in milliseconds. | `:-2\r\n` (missing), `:-1\r\n` (no TTL), or `:<ms>\r\n` | `!=1` arg errors | `PTTL k` &rarr; `:4800\r\n` |
| `RANDOMKEY` | `RANDOMKEY`<br>Returns a random existing key from database. | `$<len>\r\n<key>\r\n` (or `$-1\r\n` if empty) | `!=0` args errors | `RANDOMKEY` &rarr; `$4\r\nuser\r\n` |
| `RENAME` | `RENAME key newkey`<br>Renames key to newkey, overwriting existing newkey. | `+OK\r\n` | Missing key: `-ERR no such key\r\n` | `RENAME old new` &rarr; `+OK\r\n` |
| `RENAMENX` | `RENAMENX key newkey`<br>Renames key to newkey only if newkey does not exist. | `:1\r\n` (renamed)<br>`:0\r\n` (newkey exists) | Missing key: `-ERR no such key\r\n` | `RENAMENX old new` &rarr; `:1\r\n` |
| `RESTORE` | `RESTORE key ttl serialized-value [REPLACE] [ABSTTL] [IDLETIME s] [FREQ f]` | `+OK\r\n` | Target exists / syntax errors | `RESTORE k 0 "\x00\xc0..." REPLACE` &rarr; `+OK\r\n` |
| `SCAN` | `SCAN cursor [MATCH pattern] [COUNT count] [TYPE type]`<br>Incrementally iterates keys. | `*2\r\n$<len>\r\n<next_cursor>\r\n*<keys_array>\r\n` | Syntax/cursor errors | `SCAN 0 MATCH user:*` &rarr; `*2\r\n$1\r\n0\r\n*1\r\n$6\r\nuser:1\r\n` |
| `SORT` | `SORT key [BY pattern] [LIMIT off count] [GET pat ...] [ASC\|DESC] [ALPHA] [STORE dst]` | `*<elements>\r\n` (or `:<count_stored>\r\n` if STORE) | Syntax/type errors | `SORT list ALPHA` &rarr; `*2\r\n$1\r\na\r\n$1\r\nb\r\n` |
| `SORT_RO` | `SORT_RO key [BY pattern] [LIMIT off count] [GET pat ...] [ASC\|DESC] [ALPHA]` | `*<elements>\r\n` | Read-only sort syntax errors | `SORT_RO list ALPHA` &rarr; `*2\r\n$1\r\na\r\n$1\r\nb\r\n` |
| `TOUCH` | `TOUCH key [key ...]`<br>Alters last access time of key(s). | `:<count_keys_touched>\r\n` | `<1` arg errors | `TOUCH k1 k2` &rarr; `:2\r\n` |
| `TTL` | `TTL key`<br>Returns remaining TTL in seconds. | `:-2\r\n` (missing), `:-1\r\n` (no TTL), or `:<seconds>\r\n` | `!=1` arg errors | `TTL k` &rarr; `:58\r\n` |
| `TYPE` | `TYPE key`<br>Returns string representation of key data type. | `+string\r\n`, `+list\r\n`, `+set\r\n`, `+zset\r\n`, `+hash\r\n`, `+stream\r\n`, `+none\r\n` | `!=1` arg errors | `TYPE k` &rarr; `+string\r\n` |
| `UNLINK` | `UNLINK key [key ...]`<br>Asynchronously deletes key(s). | `:<count_keys_unlinked>\r\n` | `<1` arg errors | `UNLINK k1 k2` &rarr; `:2\r\n` |
| `WAIT` | `WAIT numreplicas timeout`<br>Blocks until writes reach replicas. | `:<numreplicas_reached>\r\n` | Arity/integer errors | `WAIT 1 1000` &rarr; `:1\r\n` |
| `WAITAOF` | `WAITAOF numlocal numreplicas timeout`<br>Blocks until previous writes are synced to local AOF and replicas. | `*2\r\n:<numlocal_synced>\r\n:<numreplicas_synced>\r\n` | Arity/integer errors | `WAITAOF 1 0 1000` &rarr; `*2\r\n:1\r\n:0\r\n` |

### 6.9 Server & Connection Management Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `AUTH` | `AUTH [username] password`<br>Authenticates connection. | `+OK\r\n` | Invalid password errors | `AUTH secretpass` &rarr; `+OK\r\n` |
| `BGREWRITEAOF` | `BGREWRITEAOF`<br>Triggers background AOF rewrite/compaction. | `+Background append only file rewriting started\r\n` | None | `BGREWRITEAOF` &rarr; `+Background append only file rewriting started\r\n` |
| `BGSAVE` | `BGSAVE [SCHEDULE]`<br>Asynchronously saves database state to disk. | `+Background saving started\r\n` | None | `BGSAVE` &rarr; `+Background saving started\r\n` |
| `CLIENT` | `CLIENT LIST\|ID\|GETNAME\|SETNAME\|KILL\|NO-EVICT\|PAUSE\|REPLY\|TRACKING\|INFO` | Subcommand-specific RESP response (`+OK`, strings, arrays) | Syntax/subcommand errors | `CLIENT SETNAME myapp` &rarr; `+OK\r\n`<br>`CLIENT ID` &rarr; `:42\r\n` |
| `COMMAND` | `COMMAND [COUNT\|DOCS\|GETKEYS\|INFO\|LIST]`<br>Returns driver command metadata. | `*<commands_array>\r\n` or command details | None | `COMMAND COUNT` &rarr; `:217\r\n` |
| `CONFIG` | `CONFIG GET\|SET\|RESETSTAT\|REWRITE parameter [value]`<br>Manages configuration. | `*<key_value_pairs>\r\n` or `+OK\r\n` | Syntax/parameter errors | `CONFIG GET maxmemory` &rarr; `*2\r\n$9\r\nmaxmemory\r\n$1\r\n0\r\n` |
| `DBSIZE` | `DBSIZE`<br>Returns total key count in currently selected database. | `:<key_count>\r\n` | `!=0` args errors | `DBSIZE` &rarr; `:150\r\n` |
| `ECHO` | `ECHO message`<br>Echoes message back to client. | `$<len>\r\n<message>\r\n` | `!=1` arg errors | `ECHO "hello"` &rarr; `$5\r\nhello\r\n` |
| `FLUSHALL` | `FLUSHALL [ASYNC\|SYNC]`<br>Deletes all keys from all databases and truncates AOF. | `+OK\r\n` | Syntax errors | `FLUSHALL` &rarr; `+OK\r\n` |
| `FLUSHDB` | `FLUSHDB [ASYNC\|SYNC]`<br>Deletes all keys from currently selected database. | `+OK\r\n` | Syntax errors | `FLUSHDB` &rarr; `+OK\r\n` |
| `HELLO` | `HELLO [protover [AUTH user pwd] [SETNAME name]]`<br>Handshake & switches RESP2/RESP3. | `*<server_info_map_or_array>\r\n` | Version/auth errors | `HELLO 3` &rarr; `*14\r\n$6\r\nserver\r\n$7\r\npyedis...` |
| `INFO` | `INFO [section [section ...]]`<br>Returns server statistics and information. | `$<len>\r\n<info_string>\r\n` | None | `INFO server` &rarr; `$45\r\n# Server\r\npyedis_version:1.0.0...` |
| `LASTSAVE` | `LASTSAVE`<br>Returns Unix timestamp of last successful save to disk. | `:<unix_timestamp>\r\n` | `!=0` args errors | `LASTSAVE` &rarr; `:1724623200\r\n` |
| `LATENCY` | `LATENCY DOCTOR\|GRAPH\|HISTORY\|LATEST\|RESET [event]` | Latency reports or `+OK\r\n` | Subcommand errors | `LATENCY LATEST` &rarr; `*0\r\n` |
| `LOLWUT` | `LOLWUT [VERSION version]`<br>Renders computer art piece. | `$<len>\r\n<art_string>\r\n` | None | `LOLWUT` &rarr; `$32\r\npyedis: Redis ver. 7 compatible\r\n` |
| `MEMORY` | `MEMORY DOCTOR\|MALLOC-STATS\|PURGE\|STATS\|USAGE key [SAMPLES count]` | Memory report or integer bytes | Subcommand errors | `MEMORY USAGE k` &rarr; `:64\r\n` |
| `MONITOR` | `MONITOR`<br>Streams back all commands processed by server in real time. | `+OK\r\n` (enters streaming mode) | None | `MONITOR` &rarr; `+OK\r\n` |
| `PING` | `PING [message]`<br>Tests connection liveness. | 0 args: `+PONG\r\n`<br>1 arg: `$<len>\r\n<msg>\r\n` | `>1` args errors | `PING` &rarr; `+PONG\r\n`<br>`PING "hi"` &rarr; `$2\r\nhi\r\n` |
| `QUIT` | `QUIT`<br>Closes connection. | `+OK\r\n` (closes TCP connection) | `!=0` args errors | `QUIT` &rarr; `+OK\r\n` |
| `REPLICAOF` | `REPLICAOF host port` / `REPLICAOF NO ONE`<br>Configures server replication target (or standalone master). | `+OK\r\n` | Arity/port errors | `REPLICAOF NO ONE` &rarr; `+OK\r\n` |
| `RESET` | `RESET`<br>Resets connection state (watches, subscriptions, transactions). | `+RESET\r\n` | `!=0` args errors | `RESET` &rarr; `+RESET\r\n` |
| `ROLE` | `ROLE`<br>Returns replication role of instance. | `*3\r\n$6\r\nmaster\r\n:0\r\n*0\r\n` | `!=0` args errors | `ROLE` &rarr; `*3\r\n$6\r\nmaster\r\n:0\r\n*0\r\n` |
| `SAVE` | `SAVE`<br>Synchronously saves database to disk. | `+OK\r\n` | None | `SAVE` &rarr; `+OK\r\n` |
| `SELECT` | `SELECT index`<br>Changes selected database (0-15). | `+OK\r\n` | Invalid index errors | `SELECT 1` &rarr; `+OK\r\n` |
| `SHUTDOWN` | `SHUTDOWN [NOSAVE\|SAVE] [NOW] [FORCE] [ABORT]`<br>Shuts down server gracefully. | Server flushes and exits 0 | None | `SHUTDOWN` &rarr; (terminates process) |
| `SLAVEOF` | `SLAVEOF host port` / `SLAVEOF NO ONE`<br>Legacy alias for `REPLICAOF`. | `+OK\r\n` | Arity/port errors | `SLAVEOF NO ONE` &rarr; `+OK\r\n` |
| `SLOWLOG` | `SLOWLOG GET [count]\|LEN\|RESET`<br>Manages slow query log. | `*<slowlog_entries>\r\n` or `:<count>\r\n` or `+OK\r\n` | Subcommand errors | `SLOWLOG LEN` &rarr; `:0\r\n` |
| `TIME` | `TIME`<br>Returns current server time as `[unix_seconds_str, microseconds_str]`. | `*2\r\n$<len>\r\n<sec>\r\n$<len>\r\n<usec>\r\n` | `!=0` args errors | `TIME` &rarr; `*2\r\n$10\r\n1724623200\r\n$6\r\n123456\r\n` |

### 6.10 Transaction Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `MULTI` | `MULTI`<br>Marks the start of a transaction block. Subsequent commands are queued. | `+OK\r\n` | Nested MULTI: `-ERR MULTI calls can not be nested\r\n` | `MULTI` &rarr; `+OK\r\n` |
| `EXEC` | `EXEC`<br>Executes all queued commands in transaction block atomically. | `*<count>\r\n<reply1>...`<br>`*-1\r\n` (if watched key modified) | Without MULTI: `-ERR EXEC without MULTI\r\n` | `EXEC` &rarr; `*2\r\n+OK\r\n:1\r\n` |
| `DISCARD` | `DISCARD`<br>Flushes all queued commands in transaction and exits transaction state. | `+OK\r\n` | Without MULTI: `-ERR DISCARD without MULTI\r\n` | `DISCARD` &rarr; `+OK\r\n` |
| `WATCH` | `WATCH key [key ...]`<br>Marks keys to be monitored for conditional execution of transaction. | `+OK\r\n` | `<1` arg: `-ERR wrong number of arguments...` | `WATCH balance` &rarr; `+OK\r\n` |
| `UNWATCH` | `UNWATCH`<br>Flushes all watched keys for current connection. | `+OK\r\n` | `!=0` args errors | `UNWATCH` &rarr; `+OK\r\n` |

### 6.11 Pub/Sub Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `SUBSCRIBE` | `SUBSCRIBE channel [channel ...]`<br>Subscribes client to specified channels. | `*3\r\n$9\r\nsubscribe\r\n$<len>\r\n<chan>\r\n:<sub_count>\r\n` | `<1` arg errors | `SUBSCRIBE news` &rarr; `*3\r\n$9\r\nsubscribe\r\n$4\r\nnews\r\n:1\r\n` |
| `UNSUBSCRIBE` | `UNSUBSCRIBE [channel [channel ...]]`<br>Unsubscribes client from channels. | `*3\r\n$11\r\nunsubscribe\r\n$<len>\r\n<chan>\r\n:<sub_count>\r\n` | None | `UNSUBSCRIBE news` &rarr; `*3\r\n$11\r\nunsubscribe\r\n$4\r\nnews\r\n:0\r\n` |
| `PSUBSCRIBE` | `PSUBSCRIBE pattern [pattern ...]`<br>Subscribes client to glob patterns. | `*3\r\n$10\r\npsubscribe\r\n$<len>\r\n<pattern>\r\n:<sub_count>\r\n` | `<1` arg errors | `PSUBSCRIBE news.*` &rarr; `*3\r\n$10\r\npsubscribe\r\n$6\r\nnews.*\r\n:1\r\n` |
| `PUNSUBSCRIBE` | `PUNSUBSCRIBE [pattern [pattern ...]]`<br>Unsubscribes client from patterns. | `*3\r\n$12\r\npunsubscribe\r\n$<len>\r\n<pattern>\r\n:<sub_count>\r\n` | None | `PUNSUBSCRIBE news.*` &rarr; `*3\r\n$12\r\npunsubscribe\r\n$6\r\nnews.*\r\n:0\r\n` |
| `PUBLISH` | `PUBLISH channel message`<br>Posts message to given channel, returning receiver count. | `:<count_of_clients_receiving_message>\r\n` | `!=2` args errors | `PUBLISH news "hello"` &rarr; `:1\r\n` |
| `PUBSUB` | `PUBSUB CHANNELS\|NUMSUB\|NUMPAT\|SHARDCHANNELS\|SHARDNUMSUB [args]` | Subcommand-specific inspection arrays/integers | Syntax errors | `PUBSUB CHANNELS` &rarr; `*1\r\n$4\r\nnews\r\n` |
| `SSUBSCRIBE` | `SSUBSCRIBE shardchannel [shardchannel ...]`<br>Subscribes to shard channel. | `*3\r\n$10\r\nssubscribe\r\n$<len>\r\n<chan>\r\n:<sub_count>\r\n` | `<1` arg errors | `SSUBSCRIBE orders` &rarr; `*3\r\n$10\r\nssubscribe\r\n$6\r\norders\r\n:1\r\n` |
| `SUNSUBSCRIBE` | `SUNSUBSCRIBE [shardchannel [shardchannel ...]]`<br>Unsubscribes from shard channel. | `*3\r\n$12\r\nsunsubscribe\r\n$<len>\r\n<chan>\r\n:<sub_count>\r\n` | None | `SUNSUBSCRIBE orders` &rarr; `*3\r\n$12\r\nsunsubscribe\r\n$6\r\norders\r\n:0\r\n` |
| `SPUBLISH` | `SPUBLISH shardchannel message`<br>Publishes message to shard channel. | `:<count_of_clients_receiving>\r\n` | `!=2` args errors | `SPUBLISH orders "new"` &rarr; `:1\r\n` |

### 6.12 Scripting & Function Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `EVAL` | `EVAL script numkeys [key [key ...]] [arg [arg ...]]`<br>Executes Lua script on server. | Result of script mapped to RESP | Script execution errors: `-ERR Error running script...` | `EVAL "return redis.call('GET', KEYS[1])" 1 k` &rarr; `$3\r\nval\r\n` |
| `EVALSHA` | `EVALSHA sha1 numkeys [key [key ...]] [arg [arg ...]]`<br>Executes cached script by SHA1. | Result of script mapped to RESP | Missing script: `-NOSCRIPT No matching script...` | `EVALSHA <sha1> 1 k` &rarr; `$3\r\nval\r\n` |
| `EVAL_RO` | `EVAL_RO script numkeys [key [key ...]] [arg [arg ...]]`<br>Read-only script execution. | Result of script | Mutation attempt in RO mode errors | `EVAL_RO "return 42" 0` &rarr; `:42\r\n` |
| `EVALSHA_RO` | `EVALSHA_RO sha1 numkeys [key [key ...]] [arg [arg ...]]`<br>Read-only cached script. | Result of script | Missing script / mutation errors | `EVALSHA_RO <sha1> 0` &rarr; `:42\r\n` |
| `SCRIPT` | `SCRIPT EXISTS\|FLUSH\|LOAD\|KILL\|DEBUG [args]`<br>Manages script cache. | `*<1_or_0_array>\r\n` or `$<len>\r\n<sha1>\r\n` or `+OK\r\n` | Syntax/subcommand errors | `SCRIPT LOAD "return 1"` &rarr; `$40\r\ne0e1f9...` |
| `FCALL` | `FCALL function numkeys [key [key ...]] [arg [arg ...]]`<br>Invokes stored function. | Result of function mapped to RESP | Function error / not found errors | `FCALL myfunc 1 k arg1` &rarr; `+OK\r\n` |
| `FCALL_RO` | `FCALL_RO function numkeys [key [key ...]] [arg [arg ...]]`<br>Read-only function call. | Result of function | Mutation attempt in RO mode errors | `FCALL_RO myfunc 1 k arg1` &rarr; `+OK\r\n` |
| `FUNCTION` | `FUNCTION LOAD\|DELETE\|LIST\|STATS\|DUMP\|RESTORE\|FLUSH [args]` | Subcommand-specific status / library arrays | Syntax/subcommand errors | `FUNCTION LIST` &rarr; `*0\r\n` |

### 6.13 Stream Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `XADD` | `XADD key [NOMKSTREAM] [MAXLEN\|MINID [=\|~] th [LIMIT c]] *\|id field val [field val ...]` | `$<len>\r\n<entry_id_string>\r\n` (or `$-1\r\n`) | ID less than top ID errors | `XADD mystream * sensor 1 temp 22.5` &rarr; `$15\r\n1724623200000-0\r\n` |
| `XREAD` | `XREAD [COUNT count] [BLOCK ms] STREAMS key [key ...] id [id ...]` | `*<streams_array>\r\n` (or `*-1\r\n` on block timeout) | Syntax/arity errors | `XREAD COUNT 1 STREAMS mystream 0-0` &rarr; `*1\r\n*2\r\n$8\r\nmystream\r\n*1...` |
| `XRANGE` | `XRANGE key start end [COUNT count]`<br>Returns stream entries within ID range. | `*<entries_array>\r\n` | Syntax/arity errors | `XRANGE mystream - + COUNT 10` &rarr; `*1\r\n*2\r\n$15\r\n1724623200000-0...` |
| `XREVRANGE` | `XREVRANGE key end start [COUNT count]`<br>Returns entries reverse ordered by ID. | `*<entries_array>\r\n` | Syntax/arity errors | `XREVRANGE mystream + - COUNT 1` &rarr; `*1\r\n*2\r\n$15\r\n1724623200000-0...` |
| `XLEN` | `XLEN key`<br>Returns number of entries in stream. | `:<count>\r\n` (0 if missing) | `!=1` arg errors | `XLEN mystream` &rarr; `:1\r\n` |
| `XTRIM` | `XTRIM key MAXLEN\|MINID [=\|~] threshold [LIMIT count]`<br>Trims stream entries. | `:<count_of_entries_deleted>\r\n` | Syntax/arity errors | `XTRIM mystream MAXLEN 1000` &rarr; `:0\r\n` |
| `XDEL` | `XDEL key id [id ...]`<br>Removes specified entries from stream by ID. | `:<count_of_entries_deleted>\r\n` | `<2` args errors | `XDEL mystream 1724623200000-0` &rarr; `:1\r\n` |
| `XINFO` | `XINFO STREAM\|GROUPS\|CONSUMERS [args]`<br>Returns stream and group inspection data. | `*<info_array>\r\n` | Stream not found errors | `XINFO STREAM mystream` &rarr; `*14\r\n$6\r\nlength\r\n:1...` |
| `XGROUP` | `XGROUP CREATE\|CREATECONSUMER\|DELCONSUMER\|DESTROY\|SETID [args]` | `+OK\r\n` or `:<deleted_count>\r\n` | Subcommand errors | `XGROUP CREATE mystream mygrp $ MKSTREAM` &rarr; `+OK\r\n` |
| `XREADGROUP` | `XREADGROUP GROUP group consumer [COUNT c] [BLOCK ms] [NOACK] STREAMS k ... id ...` | `*<streams_array>\r\n` | Group not found / syntax errors | `XREADGROUP GROUP mygrp c1 COUNT 1 STREAMS mystream >` &rarr; `*1...` |
| `XACK` | `XACK key group id [id ...]`<br>Acknowledges stream messages for consumer group. | `:<count_acknowledged>\r\n` | `<3` args errors | `XACK mystream mygrp 1724623200000-0` &rarr; `:1\r\n` |
| `XCLAIM` | `XCLAIM key group consumer min-idle-time id [id ...] [IDLE ms] [TIME ms] [RETRYCOUNT c]` | `*<claimed_entries>\r\n` | Syntax/arity errors | `XCLAIM mystream mygrp c2 3600000 1724623200000-0` &rarr; `*1...` |
| `XAUTOCLAIM` | `XAUTOCLAIM key group consumer min-idle-time start [COUNT count] [JUSTID]` | `*3\r\n$<len>\r\n<next_start>\r\n*<entries>\r\n*<deleted>\r\n` | Syntax/arity errors | `XAUTOCLAIM mystream mygrp c2 3600000 0-0 COUNT 1` &rarr; `*3...` |
| `XPENDING` | `XPENDING key group [[IDLE min-idle-time] start end count [consumer]]` | Summary array `*4...` or detailed entry list | Group not found errors | `XPENDING mystream mygrp` &rarr; `*4\r\n:0\r\n$-1\r\n$-1\r\n*0\r\n` |

### 6.14 HyperLogLog Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `PFADD` | `PFADD key element [element ...]`<br>Adds elements to the HyperLogLog probabilistic data structure. | `:1\r\n` (if internal register modified)<br>`:0\r\n` (if not modified) | `<2` args: `-ERR wrong number of arguments...`<br>Wrong Type: `-WRONGTYPE ...` | `PFADD visitors "user_1" "user_2"` &rarr; `:1\r\n`<br>`PFADD visitors "user_1"` &rarr; `:0\r\n` |
| `PFCOUNT` | `PFCOUNT key [key ...]`<br>Returns approximated cardinality of set(s) observed by HyperLogLog. | `:<approx_cardinality>\r\n` | `<1` arg: `-ERR wrong number of arguments...`<br>Wrong Type: `-WRONGTYPE ...` | `PFCOUNT visitors` &rarr; `:2\r\n`<br>`PFCOUNT hll1 hll2` &rarr; `:150\r\n` |
| `PFMERGE` | `PFMERGE destkey sourcekey [sourcekey ...]`<br>Merges multiple HyperLogLogs into destination key. | `+OK\r\n` | `<2` args: `-ERR wrong number of arguments...`<br>Wrong Type: `-WRONGTYPE ...` | `PFMERGE all_visitors v_mon v_tue` &rarr; `+OK\r\n` |

### 6.15 Special Semantics & Edge Cases
1. **`SET` Overwrite Behavior:** Overwriting a key with `SET key new_val` (without `EX`/`PX`/`KEEPTTL`) clears any existing expiration on that key, making it persistent (`TTL` becomes `-1`).
2. **`SET` Duration Bounds, Flag Order & PX Conversion:** `EX` requires positive integer seconds; `PX` requires positive integer milliseconds. If duration <= 0, return `-ERR value is not an integer or out of range\r\n`. Flag ordering must be flexible (e.g. `SET k v EX 10 NX` and `SET k v NX EX 10` are both valid). `PX <ms>` MUST be converted to an absolute expiration timestamp as `expire_at = clock() + ms / 1000.0` — storing the absolute `float`.
3. **`INCR`/`DECR` Initial Value & TTL:** If the key does not exist, it is initialized to `"0"` prior to modification (becoming `1` or `-1`). If the key already has an expiration, that expiration timestamp MUST be preserved after `INCR`/`DECR`.
4. **`EXPIRE` Non-Positive Durations:** If `EXPIRE key seconds` is called with `seconds <= 0`, the key MUST be deleted immediately. Returns `:1\r\n` if the key existed, `:0\r\n` otherwise.
5. **HyperLogLog Cardinality & Merge Semantics:** HyperLogLogs approximate unique item counts with a standard error of < 1%. When keys do not exist for `PFCOUNT`, returns `:0\r\n`. When `PFMERGE` runs, `destkey` receives the merged maximum register values of all `sourcekey`s.
6. **`WAITAOF` Local Durability Guarantee:** When `WAITAOF 1 0 timeout` is invoked, the server ensures all preceding writes are flushed to the local Append-Only File (`os.fsync`) before replying with `*2\r\n:1\r\n:0\r\n`.
7. **Connection Negotiation Commands:** Modern Redis drivers (`redis-py` v5+) automatically issue `COMMAND`, `INFO`, `CLIENT SETNAME`, or `HELLO` on connection. Returning valid RESP structures satisfies the handshake cleanly without erroring out.

## 7. Store Semantics & Expiration Engine

1. **Storage Structure:** In-memory multi-model storage supporting all core Redis data structures:
   - **Strings / Bitmaps:** `_strings: dict[str, str]` (raw byte-compatible strings)
   - **Lists:** `_lists: dict[str, list[str]]` (ordered sequences of elements)
   - **Hashes:** `_hashes: dict[str, dict[str, str]]` (field-value maps)
   - **Sets:** `_sets: dict[str, set[str]]` (unordered unique elements)
   - **Sorted Sets / Geospatial:** `_zsets: dict[str, dict[str, float]]` (member -> score map / geohash coordinates)
   - **HyperLogLog:** `_hll: dict[str, set[str] | bytearray]` (probabilistic registers / 64-bit hashed register arrays for `PFADD`/`PFCOUNT`/`PFMERGE`)
   - **Streams:** `_streams: dict[str, list[tuple[str, dict[str, str]]]]` (ordered message entries with IDs)
   - **Expiration Index:** `_expires: dict[str, float]` (key -> absolute Unix epoch seconds as `float`)
   - **Pub/Sub Subscriptions:** Channel and pattern subscriber queues for live message dispatching
   - **Transactions & Watchers:** Connection-level transaction buffer (`MULTI`/`EXEC`) and key version tracking (`WATCH`/`UNWATCH`)
2. **Deterministic Time Injection:** The `Store` accepts a `Clock` callable (`Callable[[], float]`, default `time.time`) via dependency injection. All TTL calculations, expiration comparisons, and AOF timestamp creations MUST use this clock.
3. **Dual-Mode Expiration Strategy:**
   - **Lazy Eviction:** On any key access across all data types, if current time $\ge$ expiration timestamp, the key is purged before completing the operation.
   - **Active Sweep:** Before executing `KEYS`, `SCAN`, `DBSIZE`, or `FLUSHALL`, the store performs an active scan to evict all expired keys so stale keys never appear in query results.
4. **Concurrency Safety:** All store mutations and queries execute under a shared `asyncio.Lock` owned by the `Store` instance, guaranteeing serialized atomic operations across concurrent client connections. The AOF `log_mutation()` call MUST happen **inside** the acquired lock, before the lock is released and before the RESP reply is written to the client. This ensures no two commands can interleave their store change and AOF append.

---

## 8. Persistence Architecture (AOF Engine)

`pyedis` implements an Append-Only File (AOF) durability engine to ensure zero data loss across restarts.

### 8.1 AOF Record Schema
Every state-modifying mutation across all data types appends exactly one JSON line to `<PYEDIS_DATA_DIR>/dump.aof`:
- `{"op":"SET","key":"<k>","value":"<v>","expire_at":<timestamp_float_or_null>}`
- `{"op":"DEL","key":"<k>"}`
- `{"op":"INCR","key":"<k>"}` / `{"op":"DECR","key":"<k>"}`
- `{"op":"EXPIRE","key":"<k>","expire_at":<timestamp_float>}`
- `{"op":"LPUSH"|"RPUSH"|"LPOP"|"RPOP","key":"<k>","elements":[...]}`
- `{"op":"HSET"|"HDEL","key":"<k>","fields":{...}}`
- `{"op":"SADD"|"SREM","key":"<k>","members":[...]}`
- `{"op":"ZADD"|"ZREM","key":"<k>","scores":{...}}`
- `{"op":"PFADD","key":"<k>","elements":[...]}`
- `{"op":"XADD","key":"<k>","id":"<id>","fields":{...}}`
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

### 10.3 REAL End-to-End Client-Server Tests (`docker-compose.e2e.yml`)

The project MUST feature REAL, containerized End-to-End Client-Server tests powered by `docker-compose.e2e.yml`. These E2E tests serve as vital, high-fidelity **feedback for the implementation**, validating that the running Python server behaves identically to a real Redis server when accessed over a real network socket by external clients.

- **Dual-Service Multi-Container Architecture (`docker-compose.e2e.yml`):**
  The `docker-compose.e2e.yml` file defines exactly two coordinated services:
  1. **The Server Service (`pyedis-server`):** The actual `pyedis` application running in a container, listening on port 6379, writing AOF persistence to a containerized volume/directory (`/tmp/pyedis_data`), and exposing health check readiness (e.g. `redis-cli ping | grep -q PONG`).
  2. **The Test Runner Service (`test-runner-e2e`):** A dedicated client test runner container (`Dockerfile.e2e`) containing Python, Bash, and Redis tools (`redis-cli`) that waits for `pyedis-server` to be healthy, connects over the Docker bridge network to `pyedis-server:6379`, and executes the complete end-to-end test suite (`tests/e2e/run_tests.sh`).

- **Implementation Feedback Loop:**
  These REAL E2E tests are not mocks or in-process simulations. They validate the system from the outside-in, providing immediate and authoritative feedback on:
  - Real TCP network connection handshakes, stream chunking, and multi-client connection handling.
  - RESP2/RESP3 protocol framing and compliance against official `redis-cli` and standard client tooling.
  - Full command semantics: `PING`, `ECHO`, `QUIT`, `SET` (with `EX`, `PX`, `NX`, `XX`), `GET`, `DEL`, `EXISTS`, `INCR`, `DECR`, `EXPIRE`, `TTL`, `KEYS`, and `FLUSHALL`.
  - Error envelopes and syntax validation over real sockets.
  - Pipelining and concatenated multi-command batch execution.
  - Server state persistence across container/server restarts.

- **Zero Host Package Requirement:** NO system packages (specifically `redis-cli`) are required on the host machine. All black-box client assertions execute strictly inside the containerized `test-runner-e2e`.
- **Parametrized Host & Port:** `tests/e2e/run_tests.sh` MUST parameterize target host and port via environment variables `REDIS_HOST` (default `127.0.0.1`) and `REDIS_PORT` (default `6379`), enabling it to run seamlessly inside `test-runner-e2e` (`REDIS_HOST=pyedis-server`) as well as on any local setup.
- **Continuous Execution:** Executed locally via `make e2e` and in CI (`.github/workflows/ci.yml`) on every push to provide fast, reliable implementation feedback.

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
The documentation must include a comprehensive reference catalogue covering ALL Redis command families:
- **String Operations:** `SET`, `GET`, `GETDEL`, `GETEX`, `GETRANGE`, `GETSET`, `LCS`, `MGET`, `MSET`, `MSETNX`, `SETEX`, `PSETEX`, `SETNX`, `SETRANGE`, `STRLEN`, `SUBSTR`, `INCR`, `DECR`, `INCRBY`, `DECRBY`, `INCRBYFLOAT`, `APPEND`.
- **Bitmaps & Bitfield:** `SETBIT`, `GETBIT`, `BITCOUNT`, `BITPOS`, `BITOP`, `BITFIELD`.
- **List Operations:** `LPUSH`, `RPUSH`, `LPUSHX`, `RPUSHX`, `LPOP`, `RPOP`, `LRANGE`, `LLEN`, `LINDEX`, `LSET`, `LINSERT`, `LREM`, `LTRIM`, `LMOVE`, `LPOS`, `RPOPLPUSH`, `BLPOP`, `BRPOP`, `BLMOVE`, `BRPOPLPUSH`.
- **Hash Operations:** `HSET`, `HGET`, `HMSET`, `HMGET`, `HGETALL`, `HDEL`, `HEXISTS`, `HKEYS`, `HVALS`, `HLEN`, `HINCRBY`, `HINCRBYFLOAT`, `HSETNX`, `HRANDFIELD`, `HSCAN`, `HSTRLEN`.
- **Set Operations:** `SADD`, `SREM`, `SMEMBERS`, `SISMEMBER`, `SMISMEMBER`, `SCARD`, `SUNION`, `SUNIONSTORE`, `SINTER`, `SINTERSTORE`, `SINTERCARD`, `SDIFF`, `SDIFFSTORE`, `SRANDMEMBER`, `SPOP`, `SMOVE`, `SSCAN`.
- **Sorted Set Operations:** `ZADD`, `ZCARD`, `ZCOUNT`, `ZDIFF`, `ZDIFFSTORE`, `ZINCRBY`, `ZINTER`, `ZINTERCARD`, `ZINTERSTORE`, `ZLEXCOUNT`, `ZMSCORE`, `ZPOPMAX`, `ZPOPMIN`, `ZRANDMEMBER`, `ZRANGE`, `ZRANGEBYSCORE`, `ZRANGEBYLEX`, `ZRANGESTORE`, `ZRANK`, `ZREM`, `ZREMRANGEBYLEX`, `ZREMRANGEBYRANK`, `ZREMRANGEBYSCORE`, `ZREVRANGE`, `ZREVRANGEBYLEX`, `ZREVRANGEBYSCORE`, `ZREVRANK`, `ZSCAN`, `ZSCORE`, `ZUNION`, `ZUNIONSTORE`, `BZPOPMIN`, `BZPOPMAX`.
- **HyperLogLog Operations:** `PFADD`, `PFCOUNT`, `PFMERGE`.
- **Geospatial Operations:** `GEOADD`, `GEODIST`, `GEOHASH`, `GEOPOS`, `GEORADIUS`, `GEORADIUSBYMEMBER`, `GEOSEARCH`, `GEOSEARCHSTORE`.
- **Generic & Key Management:** `COPY`, `DEL`, `DUMP`, `EXISTS`, `EXPIRE`, `EXPIREAT`, `EXPIRETIME`, `KEYS`, `MIGRATE`, `MOVE`, `OBJECT`, `PERSIST`, `PEXPIRE`, `PEXPIREAT`, `PEXPIRETIME`, `PTTL`, `RANDOMKEY`, `RENAME`, `RENAMENX`, `RESTORE`, `SCAN`, `SORT`, `SORT_RO`, `TOUCH`, `TTL`, `TYPE`, `UNLINK`, `WAIT`, `WAITAOF`.
- **Server & Connection Management:** `AUTH`, `BGREWRITEAOF`, `BGSAVE`, `CLIENT`, `COMMAND`, `CONFIG`, `DBSIZE`, `ECHO`, `FLUSHALL`, `FLUSHDB`, `HELLO`, `INFO`, `LASTSAVE`, `LATENCY`, `LOLWUT`, `MEMORY`, `MONITOR`, `PING`, `QUIT`, `REPLICAOF`, `RESET`, `ROLE`, `SAVE`, `SELECT`, `SHUTDOWN`, `SLAVEOF`, `SLOWLOG`, `TIME`.
- **Transactions:** `MULTI`, `EXEC`, `DISCARD`, `WATCH`, `UNWATCH`.
- **Pub/Sub:** `SUBSCRIBE`, `UNSUBSCRIBE`, `PSUBSCRIBE`, `PUNSUBSCRIBE`, `PUBLISH`, `PUBSUB`, `SSUBSCRIBE`, `SUNSUBSCRIBE`, `SPUBLISH`.
- **Scripting & Functions:** `EVAL`, `EVALSHA`, `EVAL_RO`, `EVALSHA_RO`, `SCRIPT`, `FCALL`, `FCALL_RO`, `FUNCTION`.
- **Streams:** `XADD`, `XREAD`, `XRANGE`, `XREVRANGE`, `XLEN`, `XTRIM`, `XDEL`, `XINFO`, `XGROUP`, `XREADGROUP`, `XACK`, `XCLAIM`, `XAUTOCLAIM`, `XPENDING`.

### 11.5 Level of Compatibility with Redis
The documentation must explicitly explain the full compatibility level of `pyedis`:
- **100% Full Redis Standalone Command Suite Implementation:** Every standard Redis command across all data structures (Strings, Bitmaps, Lists, Hashes, Sets, Sorted Sets, HyperLogLog, Geospatial, Streams, Keys, Server, Connection, Transactions, Pub/Sub, Scripting) is implemented, guaranteeing zero missing command exceptions for standalone Redis applications and test suites.
- **100% Wire Protocol Compatibility (RESP2 & RESP3):** Exact framing parity for Simple Strings (`+`), Errors (`-`), Integers (`:`), Bulk Strings (`$`), and Arrays (`*`), along with inline command parsing and RESP3 map/set/null data types.
- **100% Client Library Compatibility:** Seamless interoperability with standard tools (`redis-cli`, `redis-py` v5+, `ioredis`, Go `go-redis`, Spring Data Redis, etc.).
- **Deterministic Semantics Parity:** Identical command names (case-insensitive), error message envelopes (`-ERR ...`, `-WRONGTYPE ...`), return formats, arity checks, and expiration behavior.
- **Durability Model:** Append-Only File (`dump.aof`) with JSON-formatted records and absolute epoch timestamps (`expire_at`), guaranteeing durability without snapshotting overhead.

### 11.6 Documentation Files & Structure
- **`README.md`**: Main repository guide featuring overview, quick start, installation, use cases, command table, compatibility matrix, and developer commands (`make test`, `make lint`, `make e2e`).
- **`docs/index.md`**: Entry point for Read the Docs covering architecture, key features, getting started, and design philosophy.
- **`docs/api.md`**: Detailed technical reference covering RESP specification, full command reference, AOF persistence mechanics, and Redis compatibility comparison.
- **`.readthedocs.yaml`**: Standard configuration file for Read the Docs builds.

---

## 12. Definition of Done (DoD)

To consider `pyedis` fully implemented, the project must satisfy:
1. **Full Redis Standalone Command Suite & Public RESP API Compatibility:** Complete implementation of all 217 Redis commands across all data types (Strings, Lists, Hashes, Sets, Sorted Sets, HyperLogLog, Streams, Bitmaps, Geospatial, Keys, Server, Connection, Transactions, Pub/Sub, Scripting) operating on port 6379, passing all command assertions via official `redis-cli` and `redis-py` (v5+).
2. **Persistence & Durability Invariant:** AOF persistence engine logs mutations across all data structures with absolute `expire_at` timestamps, tolerates corrupt trailing lines, and successfully restores state on restart.
3. **Linting & Formatting Invariant (Final User Story - Best Effort):** Intermediate feature user stories MUST NOT be gated on `make lint`. A dedicated final user story ("Codebase Hardening, Formatting & Linting") is tasked with running `ruff format`, `ruff check --fix`, and resolving static typing (`mypy --strict src`). This final story operates on a **best-effort** basis: a 100% issue-free report is not required, and minor non-fatal typing/linter warnings (affecting up to 10%–20% of code lines) are permissible.
4. **Verification Criteria:** 100% test pass rate on `make test` (unit + integration executed via standard library `unittest`, ZERO `pytest` usage) and `make e2e` (REAL multi-container client-server E2E tests via `docker-compose.e2e.yml` validating the running `pyedis` service from a dedicated test runner), with >= 95% test coverage across `src/`.
5. **Comprehensive Documentation:** Complete `README.md`, `docs/index.md`, `docs/api.md`, and `.readthedocs.yaml` authored by generators with full installation instructions, usage examples, use cases, complete supported operations reference, and Redis compatibility level.
6. **GitHub Actions CI Pipeline:** `.github/workflows/ci.yml` runs on every push (and PR) across all branches, verifying that unit/integration tests and containerized E2E tests execute and pass cleanly.
