# Task: Implement In-Memory Store with Clock Injection & Dual-Mode Expiration

- **ID**: `US-002-TASK-002`
- **Story ID**: `US-002`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-002-TASK-001`
- **Target Files**: `src/store.py`, `tests/unit/test_store.py`

## Description

Implement the thread/async-safe in-memory store in `src/store.py` with corresponding unit tests in `tests/unit/test_store.py`. Support UTF-8 string key-value storage and TTL expiration tracking using an absolute epoch timestamp map. Inject deterministic clock dependency `Callable[[], float]` (defaulting to `time.time`). Implement dual-mode expiration: lazy eviction upon key access/lookup and active sweep eviction during bulk key scans (`KEYS`, `FLUSHALL`). Protect internal store state using `asyncio.Lock` to guarantee safe concurrent operation. Use PEP 585 generics throughout (`dict`, `list`, `set`, `tuple`). Write unit tests in `tests/unit/test_store.py` using a mock `FakeClock` to verify deterministic TTL decay and lazy eviction without `time.sleep` calls.
