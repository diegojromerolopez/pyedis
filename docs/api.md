# API and architecture

`resp.py` handles fragmented and pipelined RESP arrays plus inline commands. `store.py` provides an async-lock-protected dictionary and absolute expiration timestamps. `commands.py` validates and executes Redis commands. `persistence.py` writes JSON-lines AOF records and replays them at startup. `main.py` composes these components into an asyncio TCP server.

A mutation is written to `dump.aof` before its reply is transmitted. Expiration records contain absolute Unix timestamps so downtime does not renew a key's lifetime.
