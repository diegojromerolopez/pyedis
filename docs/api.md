# pyedis API & Protocol Specification

`pyedis` implements the standard Redis RESP2/RESP3 wire protocol over TCP.

## Supported Commands

- `PING [message]` - Liveness test.
- `ECHO message` - Echo string.
- `GET key` - Retrieve value.
- `SET key value [EX s] [PX ms] [NX|XX]` - Set value with optional expiration/guards.
- `DEL key [key ...]` - Delete keys.
- `EXISTS key [key ...]` - Check key existence.
- `INCR key` - Increment integer value.
- `DECR key` - Decrement integer value.
- `EXPIRE key seconds` - Set timeout.
- `TTL key` - Get remaining TTL in seconds.
- `KEYS pattern` - Find matching keys.
- `FLUSHALL` - Clear store and truncate AOF.
