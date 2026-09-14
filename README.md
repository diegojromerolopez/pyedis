# pyedis

pyedis is a small Redis-compatible RESP2 key-value server implemented with Python asyncio.

## Run

```sh
make install
make run
redis-cli -p 6379 set greeting hello
redis-cli -p 6379 get greeting
```

Supported commands are `PING`, `ECHO`, `QUIT`, `SET`, `GET`, `DEL`, `EXISTS`, `INCR`, `DECR`, `EXPIRE`, `TTL`, `KEYS`, and `FLUSHALL`. `SET` supports `EX`, `PX`, `NX`, and `XX`.

State is persisted in `data/dump.aof` using JSON lines and absolute expiration timestamps. Configure `PORT`, `PYEDIS_DATA_DIR`, and `PYEDIS_AOF_FSYNC`.

RESP uses simple strings (`+OK`), errors (`-ERR ...`), integers (`:1`), bulk strings (`$3`), and arrays (`*2`), each terminated by CRLF.

Run checks with `make build`, `make test`, `make lint`, and `make e2e`.
