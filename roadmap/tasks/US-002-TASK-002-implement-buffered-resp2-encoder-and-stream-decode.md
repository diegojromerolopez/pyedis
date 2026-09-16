# Task: Implement buffered RESP2 encoder and stream decoder

- **ID**: `US-002-TASK-002`
- **Story ID**: `US-002`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-002-TASK-001`
- **Target Files**: `src/resp.py`, `tests/unit/test_resp.py`

## Description

Implement src/resp.py as a complete RESP2 boundary with explicit encode helpers for simple strings, errors, integers, bulk strings including null bulk, and arrays, plus a stateful stream decoder that accepts arbitrary byte chunks and emits complete frames in FIFO order. Support fragmented headers, payloads, CRLF terminators, multiple frames per read, pipelining, inline CRLF-terminated whitespace-separated commands, ignored empty inline lines, binary-safe values including embedded CRLF and null bytes, empty bulk values, Unicode encoded as bytes, and nested argument arrays as required by command dispatch. Reject invalid frame types, lengths, terminators, and argument frames with a protocol-error result when safe and expose a close-required condition to the server. Add co-located unittest coverage in tests/unit/test_resp.py for every framing and failure case, asserting exact wire envelopes and no premature output. Keep the module below 500 lines and use no pytest or third-party framework.
