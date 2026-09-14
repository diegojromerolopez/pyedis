# Task: RESP Wire Protocol Engine Implementation & Unit Tests

- **ID**: `US-001-TASK-002`
- **Story ID**: `US-001`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`
- **Target Files**: `src/resp.py`, `tests/unit/test_resp.py`

## Description

Implement standard RESP2/RESP3 streaming frame decoder, chunk reassembly, pipelined buffer parser, inline string decoder, and response frame encoders (`SimpleString`, `Error`, `Integer`, `BulkString`, `NullBulkString`, `Array`, `NullArray`) in `src/resp.py`. Handle partial reads and fragmented TCP buffers cleanly. Implement co-located unit tests in `tests/unit/test_resp.py` using standard `unittest.TestCase` verifying binary-safe decoding/encoding, inline command parsing, array decoding, and fragmented TCP chunk reassembly.
