# Task: Implement Live TCP Integration & Driver Parity Suite

- **ID**: `US-002-TASK-003`
- **Story ID**: `US-002`
- **Status**: `SUCCESS`
- **Change Type**: `FEATURE`
- **Depends On**: `US-002-TASK-002`
- **Target Files**: `src/server.py`, `tests/integration/test_server.py`

## Description

Wire AOF persistence into `src/server.py` and implement comprehensive integration tests in `tests/integration/test_server.py` using `unittest.IsolatedAsyncioTestCase` and `redis-py` (v5+):
- Validate pipelined requests execute sequentially in FIFO order without lost responses.
- Run 50 concurrent `asyncio` client tasks sending `INCR counter` to ensure thread/coroutine race condition safety resulting in final value of 50.
- Verify server process stop and restart state recovery from `dump.aof`.
