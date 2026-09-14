# API and architecture

`resp.py` incrementally decodes arrays and inline commands. `store.py` owns locked values and absolute expiration timestamps. `commands.py` validates and dispatches commands. `persistence.py` writes JSON-lines AOF records. `main.py` composes the asyncio server.

Bulk values are binary-safe on the wire. AOF replay ignores malformed records and preserves absolute expiration times across restart.
