## API

pyedis listens on loopback port 6379 and speaks RESP2. The asynchronous server serializes store operations with one lock. Keys expire lazily and successful mutations are appended to an AOF under `PYEDIS_DATA_DIR`. `SET` supports EX, PX, NX, and XX; TTL returns Redis-compatible -2 and -1 sentinel values.
