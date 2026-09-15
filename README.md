# pyedis

A small RESP2-compatible in-memory Redis-style server.

Run `make install`, then `make run`. Configuration uses `PORT`, `PYEDIS_DATA_DIR`, and `PYEDIS_AOF_FSYNC`. Validation uses `make build`, `make test`, and `make lint`. Supported commands are PING, ECHO, QUIT, SET, GET, DEL, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS, and FLUSHALL. Requests use RESP2 arrays or CRLF-terminated inline commands; values are bulk strings and mutations are persisted in `dump.aof`.
