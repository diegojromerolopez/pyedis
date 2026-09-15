# pyedis

A small Redis RESP2-compatible in-memory server.

Run with `make build`, `make test`, or `make run`. Configuration uses `PORT`, `PYEDIS_DATA_DIR`, and `PYEDIS_AOF_FSYNC`. The server supports PING, ECHO, QUIT, SET, GET, DEL, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS, and FLUSHALL, with append-only recovery in `dump.aof`.
