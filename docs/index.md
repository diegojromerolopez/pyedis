# pyedis

pyedis is an in-memory Redis-compatible RESP2 TCP server with asynchronous clients and AOF durability.

## Architecture

`resp.py` handles framing, `store.py` owns values and expiration, `commands.py` maps requests to Redis replies, `persistence.py` replays durable records, and `main.py` composes the server.
