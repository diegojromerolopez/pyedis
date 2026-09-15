# pyedis

A small Python RESP2-compatible in-memory key/value server.

Run `make build`, `make test`, then `make run`. Configuration uses `PORT`, `PYEDIS_DATA_DIR`, and `PYEDIS_AOF_FSYNC`. Supported commands include PING, ECHO, QUIT, SET, GET, DEL, EXISTS, KEYS, and FLUSHALL. RESP bulk lengths are byte lengths and AOF records are JSON lines in `dump.aof`.
