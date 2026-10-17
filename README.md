# pyedis: Native Redis RESP Key-Value Store in Python

`pyedis` is a high-performance, in-memory key-value store with a native Redis wire-protocol (RESP2/RESP3) API exposed over TCP (default port 6379), written in modern Python with strict static typing (`mypy --strict src`) and standard library tooling.

## Quick Start
```bash
make install
make run
```

## Features
- Standard RESP2/RESP3 wire protocol compatibility.
- Modern Python standard library TCP async engine (`asyncio`).
- AOF persistence with absolute unix epoch timestamps.
- Zero third-party dependencies outside development tools.
