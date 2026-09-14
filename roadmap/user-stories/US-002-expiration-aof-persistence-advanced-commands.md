# User Story: Expiration Engine, AOF Persistence & Advanced Redis Commands

**Story ID:** US-002
**Title:** Expiration Engine, AOF Persistence & Advanced Redis Commands
**Depends On:** ["US-001"]
**Change Type:** new

## Description
As a application developer using `pyedis`, I want automatic key expiration (lazy eviction and active sweep), extended command semantics (`SET EX/PX/NX/XX`, `INCR`, `DECR`, `EXPIRE`, `TTL`, `KEYS`, `FLUSHALL`), durable Append-Only File (AOF) persistence with absolute timestamps, and full `redis-py` driver and pipeline compatibility.

## Tasks
1. **Deterministic Expiration Engine & Extended Commands:** Extend `src/store.py` with an expiration index operating on epoch timestamps via injected `Clock` (`Callable[[], float]`). Implement dual-mode eviction (lazy on access, active sweep before `KEYS`/`FLUSHALL`). Extend `src/commands.py` with support for `SET EX/PX/NX/XX`, `INCR`, `DECR`, `EXPIRE`, `TTL`, `KEYS` (glob pattern matching), and `FLUSHALL`. Co-locate unit tests in `tests/unit/test_store.py` and `tests/unit/test_commands.py`.
2. **AOF Persistence & Startup Replay (`src/persistence.py`):** Implement `AOFLogger` writing valid JSON lines (`{"op":"SET","key":"k","value":"v","expire_at":12345.6}`) to `${PYEDIS_DATA_DIR}/dump.aof`. Implement `os.fsync` handling when `PYEDIS_AOF_FSYNC=true`. Implement startup replay engine that tolerates truncated trailing lines, issuing warning `pyedis: ignoring corrupt trailing AOF line`. Implement `FLUSHALL` AOF truncation. Co-locate unit tests in `tests/unit/test_persistence.py`.
3. **Live TCP Integration & Driver Parity Suite (`tests/integration/test_server.py`):** Author live TCP socket integration tests using `unittest.IsolatedAsyncioTestCase` and `redis-py` (v5+). Validate pipeline requests, 50-concurrent task race condition safety (`INCR counter`), and server process restart state recovery.

## Definition of Done (DoD)

### 1. Expiration & Command Semantics
- `SET key val EX 10` sets a key with 10 seconds TTL.
- `SET key val PX 10000` sets a key with 10000 ms TTL.
- `SET key val NX` returns `+OK\r\n` if key absent, `$-1\r\n` if key exists.
- `SET key val XX` returns `+OK\r\n` if key exists, `$-1\r\n` if key absent.
- Combining both `NX` and `XX` returns `-ERR syntax error\r\n`.
- Overwriting a key with plain `SET` clears any TTL (resets `TTL` to `-1`).
- `INCR` / `DECR` on absent key initializes key to 0 before mutating, preserving existing TTL if present.
- `EXPIRE key seconds` with `seconds <= 0` immediately deletes the key.
- `TTL key` returns remaining integer seconds, `-1` for persistent key, or `-2` for missing/expired key.
- `KEYS pattern` matches glob patterns (`*`, `?`, `[abc]`, `\*`) and executes active sweep beforehand.
- `FLUSHALL` purges all store keys and truncates `dump.aof` to zero bytes.

### 2. AOF Durability Invariant
- Every state mutation writes a JSON line containing `expire_at` as an absolute Unix timestamp.
- Replaying AOF with advanced mock clock immediately evicts keys whose `expire_at` has passed without renewing lifetime.
- Abruptly terminated trailing AOF lines log `pyedis: ignoring corrupt trailing AOF line` and load preceding valid state without crashing.

### 3. Integration & Parallel Load Safety
- 50 concurrent `asyncio` client tasks hammering `INCR counter` result in final value of exactly 50.
- `redis-py` pipelines execute sequentially in FIFO order without lost replies.

### 4. Verification Criteria
- Running `python3 -m unittest discover -s tests -v` passes 100% of unit and integration tests.

```noctifab-contract
{
  "story_id": "US-002",
  "public_contracts": [
    {
      "id": "pyedis.persistence.aof",
      "interface": "AOF File System Persistence",
      "applicable_path_prefixes": ["src/", "tests/"],
      "allowed_executables": ["python3 -m unittest discover -s tests -v"],
      "exit_codes": [0],
      "stdout_contains": [],
      "stderr_prefixes": []
    }
  ]
}
```
