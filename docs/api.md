# API and entrypoints

## Process entrypoint

Start the service with `python3 -m src.main` or `make run`. `PORT` controls the
TCP listener and defaults to `6379`.

## Commands

The server supports `PING`, `ECHO`, `QUIT`, `SET`, `GET`, `DEL`, `EXISTS`,
`KEYS`, and `FLUSHALL` over RESP2. RESP requests are arrays of bulk strings.
Inline commands are also accepted; in particular, `PING` and `PING <text>` are
valid inline forms.

`PING` returns `+PONG` when no argument is supplied. With an argument it returns
that argument as a RESP bulk string. `ECHO` returns its argument. Key/value
commands operate on the in-memory store, and `FLUSHALL` clears it.

## Container surface

`docker compose up --build api` builds and starts the service. The compose file
maps host port `6379` to container port `6379`, sets `PORT=6379`, and includes a
health check used by the end-to-end harness.

## Verification

```sh
python3 -m unittest discover -s tests -v
make e2e
```
