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

---

## 2. Directory Layout & Module Responsibilities

```
pyedis/
├── pyproject.toml            # PEP 621 metadata; deps, [tool.mypy], [tool.ruff] (NO pytest)
├── requirements.txt          # Pinned runtime + dev dependencies (NO pytest)
├── Makefile                  # install, run, test, lint, format, e2e targets
├── README.md                 # Project overview, command reference, usage, e2e guide
├── .readthedocs.yaml         # Read the Docs configuration file
├── docs/                     # Read the Docs documentation directory
│   ├── index.md              # Documentation entry point & overview
│   └── api.md                # Command API, RESP protocol specification, architecture
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

## 3. Toolchain, Invocation, Exit Codes & Configuration

### 3.1 Runtime & Dev Dependencies
- **Runtime:** Standard Python 3.14+ library (`asyncio`, `dataclass`, `os`, `sys`, `time`, `typing`, `pathlib`, `json`, `signal`). No external web frameworks.
- **Dev:** `redis>=5.0`, `ruff>=0.8`, `mypy>=1.13`, `coverage>=7.6`. (NO `pytest`).
- **Testing Framework Rule (MANDATORY):** Tests MUST NOT use `pytest` or any third-party test framework under any circumstances. All unit and integration tests MUST be written using Python's standard library `unittest` framework (using `unittest.TestCase`, `unittest.IsolatedAsyncioTestCase` for async tests, and `unittest.mock`). All test modules must be executable via `python3 -m unittest discover -s tests`.

### 3.2 Makefile Targets
Every target below is REQUIRED and must be defined cleanly:
- `make install` → `python3 -m pip install -e ".[dev]"` (or `pip install -r requirements.txt`).
- `make run` → `python3 -m src.main`.
- `make test` → `python3 -m unittest discover -s tests -v` (runs unit + integration suites via standard library `unittest`; zero failures allowed; zero `pytest` usage).
- `make lint` → `ruff check src tests` AND `mypy --strict src` — both must pass with zero findings.
- `make format` → `ruff format src tests` (idempotent code formatting).
- `make e2e` → `docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from test-runner-e2e` (or host `./tests/e2e/run_tests.sh`).

### 3.3 Configuration Environment Variables
- `PORT` (default `6379`): TCP listen port for the RESP server.
- `PYEDIS_DATA_DIR` (default `./data`): Directory holding the `dump.aof` file.
- `PYEDIS_AOF_FSYNC` (default `true`): If `true`, calls `os.fsync` on the open AOF file descriptor after every state mutation before sending the RESP reply.

### 3.4 Exit Codes & Logging
- **Clean Shutdown (`SIGINT`/`SIGTERM`):** Server flushes open files, closes the TCP server socket, disconnects clients, and exits `0`.
- **Fatal Startup Error (e.g. port bound, uncreatable directory):** Log `pyedis: <reason>` to stderr and exit `1`.
- **Operational Diagnostic Logging:** All operational logs on stdout/stderr MUST use the prefix `pyedis: `.

---

## 4. RESP Wire Protocol & Framing Engine

`pyedis` communicates exclusively via standard REdis Serialization Protocol (RESP2/RESP3) over TCP.

### 4.1 RESP Frame Types & Wire Envelopes

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

### 4.2 Stream Parsing, Fragmentation, Pipelining & Inline Commands
1. **TCP Stream Buffering & Chunking:** TCP provides a continuous stream with no packet boundary guarantees. The RESP decoder must accumulate incoming chunks in a stream buffer and yield parsed commands only when complete payloads (matching byte lengths and terminating `\r\n`) are received. Incomplete frames must remain buffered without blocking or crashing.
2. **Command Pipelining:** Clients may send multiple concatenated RESP commands in a single TCP read buffer. The server must process all commands sequentially in FIFO order and return all RESP replies in matching order without dropping or interleaving frames.
3. **Multi-Bulk Arrays vs. Inline Commands:**
   - Standard client libraries (`redis-py`, `redis-cli`) send commands formatted as RESP Multi-Bulk Arrays (e.g. `*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n`).
   - Telnet, netcat, and health checkers send plain text **Inline Commands** separated by whitespace and terminated by `\r\n` (e.g. `PING\r\n`, `PING hello\r\n`, `SET k v\r\n`). The decoder must support both formats seamlessly.
4. **Binary Safety:** Bulk strings must handle arbitrary byte sequences, including UTF-8 multi-byte characters, embedded `\r\n`, whitespace, and null bytes (`\x00`).
5. **Command Case-Insensitivity:** Command names are case-insensitive (`ping`, `PING`, `Ping`, `sEt`, `gEt` must all route to the same handler). Arguments/keys retain their exact case.

---

## 5. Supported Commands & Parity Semantics

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

### 5.1 Special Semantics & Edge Cases
1. **`SET` Overwrite Behavior:** Overwriting a key with `SET key new_val` (without `EX`/`PX`) clears any existing expiration on that key, making it persistent (`TTL` becomes `-1`).
2. **`SET` Duration Bounds:** `EX` requires positive integer seconds; `PX` requires positive integer milliseconds. If duration $\le 0$, return `-ERR value is not an integer or out of range\r\n`.
3. **`INCR`/`DECR` Initial Value & TTL:** If the key does not exist, it is initialized to `"0"` prior to modification (becoming `1` or `-1`). If the key already has an expiration, that expiration timestamp MUST be preserved after `INCR`/`DECR`.
4. **`EXPIRE` Non-Positive Durations:** If `EXPIRE key seconds` is called with `seconds <= 0`, the key MUST be deleted immediately. Returns `:1\r\n` if the key existed, `:0\r\n` otherwise.
5. **Connection Negotiation Commands:** Modern Redis drivers (`redis-py` v5+) automatically issue `COMMAND`, `INFO`, or `CLIENT SETNAME` on connection. Returning `*0\r\n` or `+OK\r\n` satisfies the handshake cleanly without erroring out.

---

## 6. Store Semantics & Expiration Engine

1. **Storage Structure:** In-memory dictionary mapping UTF-8 string keys to string values, paired with an expiration map tracking absolute expiration timestamps (Unix epoch seconds as `float`).
2. **Deterministic Time Injection:** The `Store` accepts a `Clock` callable (`Callable[[], float]`, default `time.time`) via dependency injection. All TTL calculations, expiration comparisons, and AOF timestamp creations MUST use this clock.
3. **Dual-Mode Expiration Strategy:**
   - **Lazy Eviction:** On any key access (`GET`, `SET`, `DEL`, `EXISTS`, `INCR`, `DECR`, `TTL`, `EXPIRE`), if current time $\ge$ expiration timestamp, the key is purged before completing the operation.
   - **Active Sweep:** Before executing `KEYS` or `FLUSHALL`, the store performs an active scan to evict all expired keys so stale keys never appear in query results.
4. **Concurrency Safety:** All store mutations and queries execute under a shared `asyncio.Lock` owned by the `Store` instance, guaranteeing serialized atomic operations across concurrent client connections.

---

## 7. Persistence Architecture (AOF Engine)

`pyedis` implements an Append-Only File (AOF) durability engine to ensure zero data loss across restarts.

### 7.1 AOF Record Schema
Every state-modifying mutation (`SET`, `DEL`, `INCR`, `DECR`, `EXPIRE`, `FLUSHALL`) appends exactly one JSON line to `<PYEDIS_DATA_DIR>/dump.aof`:
- `{"op":"SET","key":"<k>","value":"<v>","expire_at":<timestamp_float_or_null>}`
- `{"op":"DEL","key":"<k>"}`
- `{"op":"INCR","key":"<k>"}` / `{"op":"DECR","key":"<k>"}`
- `{"op":"EXPIRE","key":"<k>","expire_at":<timestamp_float>}`
- `{"op":"FLUSHALL"}`

> [!IMPORTANT]
> **Absolute Expiration Invariant:** Expirations stored in `dump.aof` MUST use absolute Unix epoch timestamps (`expire_at`), NOT relative durations. When replaying the AOF on startup, keys whose `expire_at` has already passed are immediately evicted and not revived with fresh lifetimes.

### 7.2 Fsync & Startup Replay
1. **Fsync Guarantee:** When `PYEDIS_AOF_FSYNC=true` (default), the server calls `os.fsync()` on the open file descriptor after writing each mutation before transmitting the RESP reply.
2. **Startup Replay:** On server initialization, if `dump.aof` exists in `PYEDIS_DATA_DIR`, lines are replayed sequentially into the store.
3. **Crash Recovery & Corrupt Trailing Line Tolerance:** If the server terminated abruptly (`SIGKILL`) during a write, the final line in `dump.aof` may be truncated. The replay engine MUST log `pyedis: ignoring corrupt trailing AOF line` and load all preceding valid lines.
4. **`FLUSHALL` Truncation:** Executing `FLUSHALL` immediately truncates `dump.aof` to 0 bytes on disk.

---

## 8. Conformance & Verification Test Matrix

> [!IMPORTANT]
> **Standard Library `unittest` Conformance Requirement:**
> All test modules must subclass `unittest.TestCase` (or `unittest.IsolatedAsyncioTestCase`) and run via `python3 -m unittest discover -s tests -v`. Do NOT import or reference `pytest` anywhere.

### 8.1 Unit Tests (`tests/unit/`)
- **`test_resp.py` (`unittest.TestCase`):** Tests encoding and decoding of all RESP types, partial chunk reassembly, pipelined buffers, inline commands, and binary safety.
- **`test_store.py` (`unittest.TestCase`):** Tests set, get, del, incr, decr, ttl, active sweep, and lazy eviction using an injected mock clock.
- **`test_commands.py` (`unittest.TestCase`):** Tests arity checking, unknown commands, case-insensitivity, syntax errors, `NX`/`XX`, and `EX`/`PX`.
- **`test_persistence.py` (`unittest.TestCase`):** Tests AOF append, startup replay, absolute expiration replay, corrupted trailing line tolerance, and `FLUSHALL` truncation.

### 8.2 Integration Tests (`tests/integration/`)
- **`test_server.py` (`unittest.IsolatedAsyncioTestCase`):** Spins up a live `pyedis` TCP server on an ephemeral port.
  - Raw socket interactions.
  - Full official `redis-py` (v5+) command test suite.
  - `redis-py` pipeline execution (`pipe = r.pipeline(); ...; pipe.execute()`).
  - Concurrent load (50 concurrent async tasks hammering `INCR`).
  - Server restart durability verification.

### 8.3 Black-Box E2E Tests (`tests/e2e/`)
- **`run_tests.sh` & `docker-compose.e2e.yml`:** Executes black-box `redis-cli` assertions against a live running container or host instance, verifying identical behavior to official Redis 7.x.

### 8.4 Coverage Gate
Total test coverage of `src/` must be $\ge 95\%$ lines (`coverage run -m unittest discover -s tests && coverage report`).

---

## 9. Documentation Requirements

1. **`README.md`**: Must exist at root level documenting: installation, running the server, the full command API table, RESP wire format envelopes, AOF format, `make test`/`lint`/`e2e`, and `redis-cli` usage examples.
2. **`docs/` Folder**: Must contain documentation in Read the Docs format (`docs/index.md`, `docs/api.md`) covering Architecture, Protocol Reference, Store & Expiration Engine, Persistence, and Deployment.
3. **`.readthedocs.yaml`**: Must exist at root level configured to build the `docs/` documentation bundle.

---

## 10. Definition of Done (DoD)

To consider `pyedis` fully implemented, the project must satisfy:
1. **Public RESP API & CLI Compatibility:** Native Redis RESP2/RESP3 wire-protocol TCP server operating on port 6379, passing all command assertions via official `redis-cli` and `redis-py` (v5+).
2. **Persistence & Durability Invariant:** AOF persistence engine logs mutations with absolute `expire_at` timestamps, tolerates corrupt trailing lines, and successfully restores state on restart.
3. **Linting Invariant:** Zero findings under `ruff check src tests` AND `mypy --strict src`.
4. **Verification Criteria:** 100% test pass rate on `make test` (unit + integration executed via standard library `unittest`, ZERO `pytest` usage) and `make e2e`, with $\ge 95\%$ test coverage across `src/`.
