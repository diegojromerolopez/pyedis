# Task: Implement RESP Wire Protocol Engine and Streaming Buffer Parser

- **ID**: `US-002-TASK-001`
- **Story ID**: `US-002`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-001-TASK-001`
- **Target Files**: `src/resp.py`, `tests/unit/test_resp.py`

## Description

Implement complete RESP protocol parsing and serialization in `src/resp.py` along with unit tests in `tests/unit/test_resp.py`. Support encoding/decoding of Simple Strings (`+`), Errors (`-`), Integers (`:`), Bulk Strings (`$`), Null Bulk Strings (`$-1\r\n`), Arrays (`*`), Null Arrays (`*-1\r\n`), Empty Arrays (`*0\r\n`), and inline text commands (e.g., `PING\r\n`). Implement a streaming buffer class/parser capable of consuming arbitrary TCP byte chunks, reassembling split frames, handling binary payloads containing embedded `\r\n` or `\x00`, and yielding parsed RESP data structures in exact FIFO order. Ensure all type hints use PEP 585 standard library generics (`list`, `dict`, `tuple`, `set`). Include co-located unit tests verifying chunked buffer reassembly, pipeline decoding, and binary safety.
