# Task: Implement Command Router & Dispatcher with Full Redis Command Suite

- **ID**: `US-003-TASK-002`
- **Story ID**: `US-003`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-003-TASK-001`
- **Target Files**: `src/commands.py`, `tests/unit/test_commands.py`

## Description

Implement `CommandDispatcher` in `src/commands.py` handling case-insensitive routing and strict arity checks yielding `-ERR wrong number of arguments for '<cmd>' command\r\n`. Implement command handlers for PING, ECHO, QUIT, SET (with EX, PX, NX, XX flags), GET, DEL, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS (glob matching), and FLUSHALL. Ensure syntax error envelopes matching Redis protocol specs (`-ERR syntax error\r\n`, `-ERR value is not an integer or out of range\r\n`, `-ERR unknown command '<NAME>'\r\n`). Integrate write operations with `AOFEngine`. Add unit tests in `tests/unit/test_commands.py` covering all command options, error envelopes, and persistence dispatch.
