# API and deployment

Supported commands are PING, ECHO, QUIT, SET, GET, DEL, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS, and FLUSHALL. Requests may be RESP arrays or CRLF-terminated inline commands. Replies use RESP simple strings, errors, integers, bulk strings, and arrays.

Expiration timestamps are absolute Unix timestamps in `data/dump.aof`; replay discards already-expired values. Run with `make run`, select a port with `PORT`, and select the data directory with `PYEDIS_DATA_DIR`. Use `redis-cli -p 6379` for interoperability.
