# pyedis Documentation

`pyedis` is a high-performance, in-memory key-value store with a native Redis wire-protocol (RESP2/RESP3) API exposed over TCP (default port `6379`), written in Python 3.12+.

## Installation & Setup

To install dependencies:
```bash
make install
```

To run the server locally:
```bash
make run
```

To run unit tests and linters:
```bash
make test
make lint
```

## Architecture & AOF Durability

State-modifying mutations log to `dump.aof` with absolute Unix epoch timestamps (`expire_at`), ensuring expired keys are never resurrected on restart and tolerating corrupt trailing lines.

## Redis Client Compatibility

`pyedis` is compatible with standard `redis-cli` and `redis-py` (v5+) client libraries, supporting connection handshakes (`PING`, `COMMAND`, `INFO`, `CLIENT`).
