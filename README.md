# pyedis

A small Redis-compatible RESP2 server implemented with Python asyncio.

## Run

`make install && make run` starts port 6379. Use `redis-cli ping`, `redis-cli set key value`, `redis-cli get key`, and `redis-cli ttl key`.

Supported commands: PING, ECHO, QUIT, SET (EX/PX/NX/XX), GET, DEL, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS, and FLUSHALL. Replies use RESP simple strings, errors, integers, bulk strings, and arrays. State is appended to `data/dump.aof`; expiration records contain absolute Unix timestamps.

`make test`, `make lint`, and `make e2e` run verification targets.
