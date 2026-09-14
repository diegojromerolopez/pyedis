# User Story 003: Redis Command Dispatcher & Absolute Timestamp AOF Persistence Engine

**Story ID:** US-003  
**Title:** Redis Command Dispatcher & Absolute Timestamp AOF Persistence Engine  
**depends_on:** ["US-001"]  
**change_type:** new  

## Description
As a database user, I want a complete suite of Redis commands (`PING`, `ECHO`, `QUIT`, `SET`, `GET`, `DEL`, `EXISTS`, `INCR`, `DECR`, `EXPIRE`, `TTL`, `KEYS`, `FLUSHALL`) and append-only file (AOF) durability so that my state modifications persist across server restarts.

## Functional Requirements & Subsystems
1. **Command Router & Dispatcher (`src/commands.py`):**
   - Case-insensitive routing for supported commands.
   - Strict arity verification yielding `-ERR wrong number of arguments for '<cmd>' command\r\n` on mismatch.
   - Support `SET` options: `EX seconds`, `PX ms`, `NX`, `XX` flags with exact error replies (`-ERR syntax error\r\n`, `-ERR value is not an integer or out of range\r\n`).
   - Implement `INCR`/`DECR` (initializes missing key to 0, preserves existing TTL), `EXISTS` (multi-key sum), `DEL` (returns deleted count), `KEYS` (glob pattern matching), and `FLUSHALL`.
   - Unrecognized commands return `-ERR unknown command '<NAME>'\r\n`.
2. **AOF Persistence Engine (`src/persistence.py`):**
   - Log state-modifying mutations as single JSON lines into `<PYEDIS_DATA_DIR>/dump.aof` with absolute epoch timestamp `expire_at`.
   - Call `os.fsync()` after each write when `PYEDIS_AOF_FSYNC=true`.
   - Startup replay sequential execution into `Store`. Truncated/corrupt trailing line logs `pyedis: ignoring corrupt trailing AOF line` and restores preceding valid state.
   - `FLUSHALL` truncates `dump.aof` to zero bytes.

## Definition of Done (DoD)
- **Command Parity:** Full implementation of `PING`, `ECHO`, `QUIT`, `SET`, `GET`, `DEL`, `EXISTS`, `INCR`, `DECR`, `EXPIRE`, `TTL`, `KEYS`, `FLUSHALL` with exact Redis error envelopes.
- **Absolute Timestamp Invariant:** `dump.aof` stores absolute unix epoch timestamps (`expire_at`), preventing expired key resurrection upon replay after server restart.
- **Corrupt Recovery:** Replay engine successfully ignores corrupt trailing JSON lines caused by abrupt shutdown and logs `pyedis: ignoring corrupt trailing AOF line`.

```noctifab-contract
{
  "story_id": "US-003",
  "public_contracts": [{
    "id": "commands.persistence",
    "interface": "Command Dispatcher & AOF Engine",
    "applicable_path_prefixes": ["src/commands.py", "src/persistence.py", "tests/unit/"],
    "allowed_executables": ["python3"],
    "exit_codes": [0],
    "stdout_contains": ["OK"],
    "stderr_prefixes": []
  }]
}
```