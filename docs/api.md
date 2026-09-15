# API

pyedis accepts RESP2 arrays and inline commands over TCP. The store is serialized by one asynchronous lock and mutations are persisted to an append-only JSON file. Expiration is lazy and configuration is provided by environment variables.
