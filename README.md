# pyedis

pyedis is a small Redis-compatible RESP2 server written with the Python standard library.

## Run

```sh
make install
make run
redis-cli ping
redis-cli set answer 42
redis-cli get answer
```

The server listens on `PORT` (default `6379`) and stores its AOF at `PYEDIS_DATA_DIR/dump.aof`.
Supported commands are `PING`, `ECHO`, `QUIT`, `SET`, `GET`, `DEL`, `EXISTS`, `INCR`, `DECR`, `EXPIRE`, `TTL`, `KEYS`, and `FLUSHALL`. `SET` supports `EX`, `PX`, `NX`, and `XX`.

RESP replies use simple strings (`+OK`), errors (`-ERR ...`), integers (`:1`), bulk strings (`$3\\r\\nfoo`), and arrays (`*N`).

Run verification with `make test`, `make lint`, and `make e2e`.
