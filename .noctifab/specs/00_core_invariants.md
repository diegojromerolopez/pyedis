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
    # ... [listing truncated for roadmap decomposition] ...
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
*(Detailed command matrix partitioned into `.noctifab/specs/01_command_dispatcher_module_src_commands_py.md` — 0 commands)*

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
*(Detailed command matrix partitioned into `.noctifab/specs/02_stream_parsing_fragmentation_pipelining_inline.md` — 0 commands)*

## 6. Supported Commands & Parity Semantics

> [!IMPORTANT]
> **FULL REDIS COMMAND MANDATE: ALL COMMANDS LISTED BELOW MUST BE IMPLEMENTED**
> Every Redis command across all categories listed in this section MUST be fully implemented in `pyedis`. The server MUST NOT return `-ERR unknown command` for any of the catalogued commands. Full RESP2/RESP3 wire-protocol compatibility, parameter parsing, type validation, error envelopes, and parity semantics apply across all data types and server functions.

### 6.1 String Commands
*(Detailed command matrix partitioned into `.noctifab/specs/03_string.md` — 22 commands)*

### 6.2 Bitmaps & Bitfield Commands
*(Detailed command matrix partitioned into `.noctifab/specs/04_bitmaps_bitfield.md` — 6 commands)*

### 6.3 List Commands
*(Detailed command matrix partitioned into `.noctifab/specs/05_list.md` — 20 commands)*

### 6.4 Hash Commands
*(Detailed command matrix partitioned into `.noctifab/specs/06_hash.md` — 16 commands)*

### 6.5 Set Commands
*(Detailed command matrix partitioned into `.noctifab/specs/07_set.md` — 17 commands)*

### 6.6 Sorted Set (ZSet) Commands
*(Detailed command matrix partitioned into `.noctifab/specs/08_sorted_set_zset.md` — 33 commands)*

### 6.7 Geospatial Commands
*(Detailed command matrix partitioned into `.noctifab/specs/09_geospatial.md` — 8 commands)*

### 6.8 Generic & Key Management Commands
*(Detailed command matrix partitioned into `.noctifab/specs/10_generic_key_management.md` — 29 commands)*

### 6.9 Server & Connection Management Commands
*(Detailed command matrix partitioned into `.noctifab/specs/11_server_connection_management.md` — 28 commands)*

### 6.10 Transaction Commands
*(Detailed command matrix partitioned into `.noctifab/specs/12_transaction.md` — 5 commands)*

### 6.11 Pub/Sub Commands
*(Detailed command matrix partitioned into `.noctifab/specs/13_pub_sub.md` — 9 commands)*

### 6.12 Scripting & Function Commands
*(Detailed command matrix partitioned into `.noctifab/specs/14_scripting_function.md` — 8 commands)*

### 6.13 Stream Commands
*(Detailed command matrix partitioned into `.noctifab/specs/15_stream.md` — 14 commands)*

### 6.14 HyperLogLog Commands
*(Detailed command matrix partitioned into `.noctifab/specs/16_hyperloglog.md` — 3 commands)*

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
*(Details partitioned into `.noctifab/specs/aux_9_phased_implementation_user_story_roadmap.md`)*

## 10. Conformance & Verification Test Matrix

*(Exhaustive per-test matrices and assertions are preserved in SPEC.md for downstream task implementation)*

## 11. Documentation Requirements & Generator Mandate
*(Details partitioned into `.noctifab/specs/aux_11_documentation_requirements_generator_mandate.md`)*

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