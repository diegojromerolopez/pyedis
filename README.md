# pyedis

Native Redis RESP Key-Value Store written in modern Python 3.14 / 3.10+.

## Features
- Native Redis wire protocol (RESP2/RESP3) over TCP
- Append-Only File (AOF) persistence with absolute TTL timestamps
- Compatible with `redis-cli` and `redis-py`
- Standard library `unittest` based test suite

## Usage
```bash
make install
make run
```

## Running Tests
```bash
make test
make lint
```
