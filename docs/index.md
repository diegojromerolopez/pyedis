# pyedis

pyedis is a small Python 3.10+ RESP2-compatible in-memory key/value server.

## Quick start

Use `make test` to run the unittest suite and `make run` to start the server.
The application entrypoint is `python3 -m src.main`. The default listening port
is `6379`; set the `PORT` environment variable to choose another port.

The repository has no required runtime framework or external runtime package.

## Protocol summary

Commands may be sent as RESP arrays or as inline text. Inline `PING` and
`PING message` are supported. RESP `PING` returns `PONG`, while a supplied
message is echoed. Supported commands are `PING`, `ECHO`, `QUIT`, `SET`, `GET`,
`DEL`, `EXISTS`, `KEYS`, and `FLUSHALL`.

Run verification with:

```sh
python3 -m unittest discover -s tests -v
```
