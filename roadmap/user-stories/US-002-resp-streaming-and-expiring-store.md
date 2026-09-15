# US-002 — RESP Streaming, Binary Safety, and Expiring Store

**depends_on:** ["US-001"]  
**change_type:** new

## User Story

As a client, I want robust RESP2 stream framing and deterministic string storage with expiration so that fragmented, pipelined, binary-safe requests behave predictably.

## Requirements

1. Implement `src/resp.py` streaming RESP2 encoder/decoder for simple strings, errors, integers, bulk/null bulk strings, arrays, fragmentation, pipelining, inline commands, and protocol errors.
2. Implement `src/store.py` with injected `Clock`, async locking, lazy expiration, active sweeps, absolute expiration, glob-compatible key enumeration, and atomic string operations.
3. Add `tests/unit/test_resp.py` and `tests/unit/test_store.py` using unittest, fake clocks, in-memory state, binary payloads, and boundary assertions.

## Definition of Done (DoD)

- **Wire contract:** byte lengths are used; embedded CRLF, null bytes, whitespace, and UTF-8 survive unchanged. Partial frames remain buffered; three concatenated commands are yielded FIFO; malformed frames return `-ERR protocol error\\r\\n`.
- **Store contract:** injected fake time proves TTL 5 at T0, 2 at T0+3, and absent/TTL -2 after expiry. Plain SET clears expiry; INCR/DECR preserve expiry; KEYS actively sweeps; EXISTS duplicate counting and deterministic lexicographic key output are supported.
- **Scenario matrix:** tests cover every RESP frame type, empty/null arrays, incomplete headers/payloads, inline PING/ECHO/SET, binary values, expiration at exact boundary, negative/zero TTL, overwrite, missing keys, glob `*`, `?`, `[abc]`, and escaped `\\*`.
- **Testing:** Chicago-school tests use real encoder/decoder/store objects and fake clocks; no live external database or broker. E2E physically exercises RESP fragmentation, pipelining, binary-safe GET/SET, KEYS patterns, and TTL behavior with readiness polling.
- **Required paths:** `src/resp.py`, `src/store.py`, `tests/unit/test_resp.py`, and `tests/unit/test_store.py` exist; no source file exceeds 500 lines.
- **Anti-stub and prohibition:** no stubs, tautological tests, `pytest`, pytest artifacts, `# type: ignore` masking, or shell error masking.
- **Verification:** all tests pass with zero failures; lint remains advisory until hardening.

```noctifab-contract
{"story_id": "US-002","public_contracts":[{"id":"resp.streaming","interface":"RESP2 TCP byte stream","applicable_path_prefixes":["src/resp.py","src/store.py","tests/unit/"],"allowed_executables":["python3 -m unittest discover -s tests -v"],"exit_codes":[0,1],"stdout_contains":[],"stderr_prefixes":["pyedis: "]}]}
```