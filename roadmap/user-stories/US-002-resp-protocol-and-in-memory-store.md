# User Story 002: RESP Wire Protocol Engine & In-Memory Store with Clock Dependency Injection

**Story ID:** US-002  
**Title:** RESP Wire Protocol Engine & In-Memory Store with Clock Dependency Injection  
**depends_on:** ["US-001"]  
**change_type:** new  

## Description
As a client application, I want `pyedis` to parse and serialize RESP2/RESP3 frames and maintain an in-memory key-value store with deterministic time-based TTL expiration so that operations are accurate, binary-safe, and thread/async-safe.

## Functional Requirements & Subsystems
1. **RESP Wire Protocol Framing (`src/resp.py`):**
   - Encode and decode Simple Strings (`+`), Errors (`-`), Integers (`:`), Bulk Strings (`$`), Null Bulk Strings (`$-1\r\n`), Arrays (`*`), Null Arrays (`*-1\r\n`), and Empty Arrays (`*0\r\n`).
   - Support TCP byte chunk reassembly, pipelined buffer parsing (yielding commands in FIFO order), and plain text inline commands (e.g. `PING\r\n`).
   - Ensure binary safety for arbitrary byte payloads including embedded `\r\n`, `\x00`, and UTF-8 content.
2. **In-Memory Store & Expiration Engine (`src/store.py`):**
   - Implement in-memory dictionary mapping UTF-8 string keys to values and an absolute epoch timestamp expiration map.
   - Inject deterministic clock dependency (`Callable[[], float]`, default `time.time`).
   - Support dual-mode expiration: lazy eviction on access and active sweep during `KEYS` or `FLUSHALL` queries.
   - Protect store state using `asyncio.Lock` for concurrency safety.

## Definition of Done (DoD)
- **Protocol Wire Envelopes:** Encodes simple strings, bulk strings, integers, arrays, and errors matching exact RESP specs.
- **Streaming & Pipeline Handling:** Concatenated RESP commands in a single TCP read buffer are decoded sequentially in exact FIFO order.
- **Mock Clock Determinism:** Unit tests in `tests/unit/test_store.py` verify lazy eviction and TTL decay using a injected mock clock (`FakeClock`) without dynamic time sleeps.
- **Type Hints:** Standard library PEP 585 generics (`dict`, `list`, `tuple`, `set`) used throughout without `typing.Dict`/`typing.List` imports.

```noctifab-contract
{
  "story_id": "US-002",
  "public_contracts": [{
    "id": "resp.protocol-store",
    "interface": "RESP Protocol Encoder/Decoder & In-Memory Store",
    "applicable_path_prefixes": ["src/resp.py", "src/store.py", "tests/unit/"],
    "allowed_executables": ["python3"],
    "exit_codes": [0],
    "stdout_contains": ["OK"],
    "stderr_prefixes": []
  }]
}
```