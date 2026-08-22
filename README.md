# `pyedis` - Native Redis RESP Key-Value Store in Python 3.14

> [!NOTE]
> `pyedis` is a software project built autonomously with **[Noctifab](https://github.com/diegojromerolopez/noctifab)**—the dark factory AI software development orchestrator.
> The starting point of the project, before running Noctifab on it, is commit [`98c130f`](https://github.com/diegojromerolopez/pyedis/commit/98c130f).

`pyedis` is a high-performance, in-memory key-value store with a **native Redis wire-protocol (RESP2/RESP3) API exposed over TCP** (default port `6379`), written in modern Python (3.14 / 3.10+) with strict static typing (`mypy --strict src`) and standard library tooling. It mirrors Redis core command semantics (`PING`, `ECHO`, `QUIT`, `SET`, `GET`, `DEL`, `EXISTS`, `INCR`, `DECR`, `EXPIRE`, `TTL`, `KEYS`, `FLUSHALL`) with deterministic RESP reply and error envelopes, and persists state to an append-only file (AOF) using absolute expiration timestamps so data and TTLs survive process restarts and sudden terminations (`SIGKILL`). Standard Redis client utilities (`redis-cli`, `redis-py` v5+) are 100% compatible with `pyedis`.

---

## ⚡ Core Technical Features & Invariants

- **🤖 Autonomous Noctifab Project**: Designed from the ground up to be developed, validated, and maintained natively by [Noctifab](https://github.com/diegojromerolopez/noctifab).
- **⚡ Native RESP2/RESP3 Wire Protocol**: Full binary-safe Redis serialization protocol parser supporting both multi-bulk arrays and whitespace-delimited inline commands (`PING\r\n`, `SET k v\r\n`).
- **🛡️ 100% Typed & Zero Linter Warnings**: Built with Python 3.10+ PEP 585 generic collections (`dict`, `list`, `tuple`, `set`), passing `ruff check src tests` and `mypy --strict src` with zero findings.
- **⏱️ Deterministic Dependency Injection (DI)**: In-memory store uses an injected `Clock` callable (`Callable[[], float]`), enabling unit tests to freeze, step, or fast-forward time without sleeping.
- **💾 Append-Only File (AOF) Persistence**: State-modifying mutations log to `dump.aof` with absolute Unix epoch timestamps (`expire_at`), ensuring expired keys are never resurrected on restart. Tolerates and recovers from corrupt trailing lines caused by abrupt termination (`SIGKILL`).
- **🔄 Lock-Protected Async Concurrency**: Serialized atomic command execution via `asyncio.Lock` across concurrent client connections and pipelined buffers.
- **🧪 Standard Library `unittest` Mandate**: All unit and integration suites use Python's built-in `unittest` (`unittest.TestCase`, `unittest.IsolatedAsyncioTestCase`, `unittest.mock`) with zero external test runner dependencies.
- **🚀 Official Redis Compatibility**: Verified against official `redis-cli` and `redis-py` (v5+) clients.

---

## 🏗️ Architecture & Component Overview

```
                      +-----------------------------+
                      |   Client (redis-cli, py)    |
                      +-----------------------------+
                                     │  (TCP :6379)
                                     ▼
                      +-----------------------------+
                      |    src/main.py (asyncio)    |
                      +-----------------------------+
                                     │  (Raw bytes)
                                     ▼
                      +-----------------------------+
                      |     src/resp.py (Parser)    |
                      +-----------------------------+
                                     │  (Parsed Command)
                                     ▼
                      +-----------------------------+
                      |   src/commands.py (Router)  |
                      +-----------------------------+
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
    +------------------------------+   +------------------------------+
    |   src/store.py (In-Memory)   |   | src/persistence.py (AOF Log) |
    |   - Dict + Expiration Map    |   |   - dump.aof (JSON Lines)    |
    |   - Injected Clock & Lock    |   |   - Absolute expire_at       |
    +------------------------------+   +------------------------------+
```

---

## 📋 Supported Commands

| Command | Signature | Description |
| :--- | :--- | :--- |
| **`PING`** | `PING [message]` | Tests connection liveness or echoes custom message |
| **`ECHO`** | `ECHO message` | Echoes the given string |
| **`QUIT`** | `QUIT` | Closes the client connection gracefully |
| **`SET`** | `SET key value [EX s] [PX ms] [NX\|XX]` | Sets string value with optional expiration and existence guards |
| **`GET`** | `GET key` | Retrieves the string value of a key |
| **`DEL`** | `DEL key [key ...]` | Deletes one or more keys |
| **`EXISTS`** | `EXISTS key [key ...]` | Returns the count of existing keys |
| **`INCR`** | `INCR key` | Increments the integer value of a key by 1 |
| **`DECR`** | `DECR key` | Decrements the integer value of a key by 1 |
| **`EXPIRE`** | `EXPIRE key seconds` | Sets an expiration timeout in seconds |
| **`TTL`** | `TTL key` | Returns remaining time-to-live in seconds (`-1` no expiry, `-2` missing) |
| **`KEYS`** | `KEYS pattern` | Finds all keys matching a glob pattern |
| **`FLUSHALL`** | `FLUSHALL` | Clears all keys from memory and truncates AOF |
| **`COMMAND`** | `COMMAND [DOCS]` | Connection handshake capability discovery |
| **`INFO`** | `INFO [section]` | Server information and driver handshake |
| **`CLIENT`** | `CLIENT SETNAME\|GETNAME` | Client connection negotiation |

---

## 🧪 Testing & Verification

### Install Dependencies
```bash
make install
```

### Run Server Locally
```bash
make run
# Or with custom port:
PORT=6380 make run
```

### Run Unit & Integration Tests (Standard Library `unittest`)
```bash
make test
```

### Run Linter & Static Type Analysis
```bash
make lint
# Runs: ruff check src tests && mypy --strict src
```

### Run Formatter
```bash
make format
# Runs: ruff format src tests
```

### Run Host E2E Black-Box Suite
With `redis-cli` installed and `pyedis` running on port 6379:
```bash
./tests/e2e/run_tests.sh
```

### Run Multi-Container Docker Compose E2E Suite
Run the containerized black-box test harness:
```bash
make e2e
# Or directly:
docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from test-runner-e2e
```

---

## ⚙️ Configuration

| Environment Variable | Default | Description |
| :--- | :--- | :--- |
| `PORT` | `6379` | TCP listen port for the RESP server |
| `PYEDIS_DATA_DIR` | `./data` | Directory where `dump.aof` is stored |
| `PYEDIS_AOF_FSYNC` | `true` | Call `os.fsync()` after every mutation |

---

## 📄 Specification

For complete architectural details, exact RESP wire formats, edge case semantics, and verification matrices, see [SPEC.md](SPEC.md).

---

## 📜 License

Licensed under the [MIT License](LICENSE).
