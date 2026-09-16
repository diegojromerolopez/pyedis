# US-002 — RESP Protocol, Command Dispatch & Core Command Surface

**depends_on:** ["US-001"]  
**change_type:** new

## User story
As a Redis client, I want complete framing and command-dispatch behavior so that pipelined, fragmented, inline, binary-safe requests receive deterministic Redis-compatible replies.

## Requirements and atomic tasks

1. Implement the RESP encoder/stream decoder in `src/resp.py` with chunk reassembly, pipelining, inline commands, binary-safe bulk values, malformed-frame handling, and unit tests in `tests/unit/test_resp.py`.
2. Implement command parsing and dispatch in `src/commands.py` for PING, ECHO, QUIT, SET option syntax, GET, DEL, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS, FLUSHALL, unknown commands, and optional discovery fallback; co-locate `tests/unit/test_commands.py` and live integration scenarios in `tests/integration/test_server.py`.

## Definition of Done (DoD)

- RESP2 replies exactly match the refined specification: simple strings, errors, integers, bulk strings, null bulk, and arrays. Pipelined replies preserve FIFO order.
- Fragmented headers, payloads, and terminators are buffered without premature output or crashes. Embedded `CRLF`, null bytes, Unicode bytes, whitespace, empty bulk values, and multiple frames in one read are tested.
- Inline commands accept CRLF-terminated whitespace-separated arguments; empty inline lines are ignored. Invalid frame types, lengths, terminators, and argument frames return `-ERR protocol error\\r\\n` when safe and close the connection.
- Command names are case-insensitive. Exact arity, unknown-command, integer, syntax, and conditional SET errors match the refined specification, including lowercase command names in arity errors and original unknown names.
- Each command has a dedicated executable black-box scenario: PING, ECHO, QUIT, SET, GET, DEL, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS, FLUSHALL, unknown command, malformed protocol, pipelining, inline input, and binary-safe values. Each asserts the complete response envelope, not merely connectivity.
- Command tests use an injected in-memory store double where the real store is not yet available; no live external database or broker is used. Time-related command tests use a deterministic fake clock.
- `src/main.py` remains a thin wrapper under 15 lines around a testable lifecycle function. No source file exceeds 500 lines.
- Pytest and all third-party test frameworks remain forbidden. No stubs, ignored errors, shell masking, or tautological tests are permitted. Intermediate linting may be advisory, but all unittest suites must pass with zero failures and exit `0`.

```noctifab-contract
{"story_id": "US-002","public_contracts":[{"id":"resp.command-dispatch","interface":"TCP RESP2/inline command stream","applicable_path_prefixes":["src/resp.py","src/commands.py","tests/"],"allowed_executables":["python3 -m src.main","python3 -m unittest discover -s tests -v"],"exit_codes":[0],"stdout_contains":[],"stderr_prefixes":["pyedis: "]}]}
```