# pyedis

pyedis is a small RESP2-compatible in-memory key/value server implemented with
Python's standard library. It has no required runtime framework or third-party
runtime dependency.

## Run locally

```sh
make build
make test
make run
```

The server listens on `PORT`, which defaults to `6379`. The `run` target invokes
`python3 -m src.main` directly. Persistence-related settings are
`PYEDIS_DATA_DIR` and `PYEDIS_AOF_FSYNC` when enabled by the server
configuration.

## Protocol

The server accepts RESP arrays of bulk strings and also supports inline commands.
Inline `PING` is accepted as `PING` or `PING hello`; RESP `PING` returns the
simple string `+PONG` and `PING message` returns the message as a bulk string.

Supported commands are `PING`, `ECHO`, `QUIT`, `SET`, `GET`, `DEL`, `EXISTS`,
`KEYS`, and `FLUSHALL`. RESP bulk lengths are measured in bytes.

## Containers

Build and run the service with:

```sh
docker compose up --build api
```

The compose configuration exposes port `6379` and sets the container `PORT` to
`6379. Run the standard-library socket smoke test with:

```sh
make e2e
```

## Verification

The complete test command is exactly:

```sh
python3 -m unittest discover -s tests -v
```
