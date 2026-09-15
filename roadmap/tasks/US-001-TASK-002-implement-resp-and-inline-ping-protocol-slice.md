# Task: Implement RESP and inline PING protocol slice

- **ID**: `US-001-TASK-002`
- **Story ID**: `US-001`
- **Status**: `PENDING`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`
- **Target Files**: `src/main.py`, `tests/integration/test_server.py`

## Description

Extend the walking-skeleton server with a concrete standard-library protocol implementation and co-located real observable socket tests. Parse inline CRLF commands and RESP2 arrays sufficiently for PING, accept case-insensitive PING, return exact `+PONG\r\n` for zero arguments, return exact bulk-string framing for one message argument such as `$5\r\nhello\r\n`, and return exact `-ERR wrong number of arguments for 'ping' command\r\n` for invalid arity. Handle fragmented socket reads and multiple complete commands safely enough for the stated scenarios, preserve clean connection/server shutdown, and retain injectable/testable server boundaries. Expand tests/integration/test_server.py with unittest.IsolatedAsyncioTestCase tests using real sockets for RESP PING, RESP message echo, inline framing, invalid arity, and lifecycle behavior. Do not introduce pytest, third-party frameworks, shell masking, pass, ellipsis, or NotImplementedError.
