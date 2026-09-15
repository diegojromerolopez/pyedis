# Refined Specification: pyedis

## 1. Product and Scope

`pyedis` is an in-memory string key-value store implemented in Python 3.14 and exposed through a TCP server speaking Redis RESP2. RESP3 negotiation is not implemented; clients requesting RESP3 with `HELLO 3` receive `-ERR unknown command 'HELLO'` unless a later compatibility extension is added. The required compatibility target is `redis-cli` and `redis-py` 5+ using RESP2 fallback behavior.

The default listen address is `127.0.0.1:6379`. Configuration is supplied by `PORT` (default `6379`), `PYEDIS_DATA_DIR` (default `./data`), and `PYEDIS_AOF_FSYNC` (default `true`, case-insensitive values `true/1/yes` and `false/0/no`).

Only the Python standard library is a runtime dependency. Development dependencies are pinned or lower-bounded as specified: `redis>=5.0`, `ruff>=0.8`, `mypy>=1.13`, and `coverage>=7.6`. `pytest` is forbidden everywhere: imports, dependencies, configuration, scripts, Makefile recipes, and documentation.

## 2. Required Repository Layout

The repository MUST contain exactly these required application and validation paths:

```
pyproject.toml
requirements.txt
Makefile
README.md
.readthedocs.yaml
docs/index.md
docs/api.md
.gitignore
docker-compose.e2e.yml
src/__init__.py
src/main.py
src/resp.py
src/store.py
src/commands.py
src/persistence.py
tests/unit/test_store.py
tests/unit/test_resp.py
tests/unit/test_commands.py
tests/unit/test_persistence.py
tests/integration/test_server.py
tests/e2e/Dockerfile
tests/e2e/run_tests.sh
data/
```

`data/` is created at runtime and ignored by git. No source file may exceed 500 lines. All source functions, methods, dataclasses, and modules are annotated with Python 3.10+ type hints using built-in generic collections rather than `typing.Dict`, `List`, `Tuple`, or `Set`. `mypy --strict src` is mandatory.

## 3. Public Entry Point, Lifecycle, and Diagnostics

`python3 -m src.main` starts the asynchronous TCP server. `src.main` is a thin wrapper delegating immediately to a testable server function. The server accepts multiple clients, processes each client stream sequentially, and serializes all store operations through one shared asynchronous lock.

Clean `SIGINT` or `SIGTERM` shutdown flushes open AOF files, closes the listening socket and active client writers, and exits with status 0. Startup failures such as an unwritable data directory or failed port bind write `pyedis: <reason>` to stderr and exit with status 1. Every diagnostic line written by the application to stdout or stderr begins with `pyedis: `. A corrupt final AOF record writes exactly `pyedis: ignoring corrupt trailing AOF line` as a warning and does not prevent startup.

## 4. Makefile and Tooling Contracts

The Makefile defines each target exactly once:

- `make install`: `python3 -m pip install -e ".[dev]"`.
- `make build`: validates the package can be imported and the server entrypoint can be compiled with `python3 -m compileall src`.
- `make run`: `python3 -m src.main`.
- `make test`: `python3 -m unittest discover -s tests -v`; zero discovered tests or any failure is an error.
- `make lint`: `ruff check src tests` followed by `mypy --strict src`.
- `make format`: `ruff format src tests`.
- `make e2e`: `docker compose -f docker-compose.e2e.yml up --build --exit-code-from e2e`.

All tests subclass `unittest.TestCase` or `unittest.IsolatedAsyncioTestCase` and use `unittest.mock` only. No third-party test framework is permitted.

## 5. RESP2 Protocol and Stream Framing

The server accepts RESP2 arrays and inline commands. Supported frame encodings are:

- Simple string: `+TEXT\r\n`.
- Error: `-ERR message\r\n`.
- Integer: `:<signed integer>\r\n`.
- Bulk string: `$<byte length>\r\n<bytes>\r\n`.
- Null bulk: `$-1\r\n`.
- Array: `*<count>\r\n<frames>...`.
- Empty array: `*0\r\n`.
- Null array: `*-1\r\n`.

Bulk lengths count bytes, not characters. Values and arguments are binary-safe and may contain UTF-8, spaces, tabs, CRLF, or null bytes. Command names are decoded case-insensitively; key and value bytes are preserved as supplied and represented as UTF-8 strings only where command semantics require strings.

The decoder buffers arbitrary TCP chunks, yields only complete frames, retains incomplete bytes, and yields all concatenated frames FIFO. Inline commands are CRLF-terminated and split on ASCII whitespace; an incomplete line remains buffered. Malformed RESP or unterminated inline input receives `-ERR protocol error\r\n`, after which the server closes that client connection. A command with a valid frame but invalid arity or syntax receives the command-specific error and the connection remains open.

`QUIT` sends `+OK\r\n`, drains the writer, and closes that client connection. Replies for pipelined commands are emitted in input order.

## 6. Commands and Exact Reply Contracts

Command names are case-insensitive. Unknown commands use the received command name normalized to uppercase in `-ERR unknown command '<NAME>'\r\n`.

- `PING [message]`: zero arguments returns `+PONG\r\n`; one returns a bulk string; more returns `-ERR wrong number of arguments for 'ping' command\r\n`.
- `ECHO message`: exactly one argument and bulk-string reply; otherwise the exact echo arity error.
- `QUIT`: exactly zero arguments returns `+OK\r\n` then closes; otherwise the exact quit arity error.
- `SET key value [EX seconds|PX milliseconds] [NX|XX]`: success `+OK\r\n`; failed NX/XX condition `$-1\r\n`; both guards, duplicate/conflicting options, missing option values, malformed options, or invalid positive integer duration return `-ERR syntax error\r\n` except duration values `<=0` or outside signed 64-bit range, which return `-ERR value is not an integer or out of range\r\n`. A plain overwrite removes prior expiry.
- `GET key`: bulk value or `$-1\r\n`; wrong arity uses the exact get arity error.
- `DEL key [key ...]`: integer count of distinct keys actually removed; wrong arity uses the exact del arity error.
- `EXISTS key [key ...]`: integer count, counting duplicate existing key arguments independently; wrong arity uses the exact exists arity error.
- `INCR key` and `DECR key`: integer result, initialize missing keys from zero, preserve existing expiry, and reject non-integers or overflow with `-ERR value is not an integer or out of range\r\n`.
- `EXPIRE key seconds`: positive duration sets expiry and returns `:1`; missing/expired key returns `:0`; duration `<=0` immediately deletes an existing key and returns `:1`, otherwise `:0`; invalid integer returns the exact integer-range error.
- `TTL key`: `:-2` for absent/expired, `:-1` for persistent, or remaining whole seconds rounded down toward zero for an expiring key; wrong arity uses the exact ttl arity error.
- `KEYS pattern`: glob matching with `*`, `?`, character classes such as `[abc]`, and backslash escaping; returns a RESP array of bulk keys in deterministic lexicographic order; no matches returns `*0\r\n`.
- `FLUSHALL`: removes all keys, truncates AOF to zero bytes, and returns `+OK\r\n`; extra arguments return `-ERR wrong number of arguments for 'flushall' command\r\n`.

For every command, mutation replies are transmitted only after required AOF persistence and optional fsync complete. `COMMAND`, `INFO`, and `CLIENT` are not supported and return their normal unknown-command error; redis-py must still operate using RESP2 fallback.

## 7. Store and Expiration

The store maps string keys to string values and tracks absolute Unix epoch `expire_at` timestamps. A clock callable defaults to `time.time` and is injectable. Every access lazily removes expired keys. `KEYS` and `FLUSHALL` additionally sweep all expired entries first. All operations, including reads, use the shared async lock. `INCR` and `DECR` preserve expiry; `SET` without expiry clears it. TTL calculations use the injected clock and never sleep in unit tests.

## 8. AOF Persistence

The AOF path is `<PYEDIS_DATA_DIR>/dump.aof`. Each successful state mutation appends exactly one JSON object per line:

```
{"op":"SET","key":"k","value":"v","expire_at":null}
{"op":"SET","key":"k","value":"v","expire_at":123.5}
{"op":"DEL","key":"k"}
{"op":"INCR","key":"k"}
{"op":"DECR","key":"k"}
{"op":"EXPIRE","key":"k","expire_at":123.5}
{"op":"FLUSHALL"}
```

A failed conditional SET, a missing-key DEL/EXPIRE, a non-positive EXPIRE on a missing key, and invalid commands append nothing. A successful mutation that changes state appends one record. Expiration timestamps are absolute. Startup replays valid records in order using the injected/current clock and does not revive expired keys. A malformed or truncated final line is ignored with the exact warning above; malformed non-final lines are a fatal startup error with `pyedis: <reason>` and exit 1. `PYEDIS_AOF_FSYNC=true` calls `os.fsync` after each append and before its reply; false skips fsync. FLUSHALL truncates the file immediately.

## 9. Testing, E2E, and Coverage

Unit and integration tests run only through `python3 -m unittest discover -s tests -v`. Integration tests may use redis-py and live ephemeral loopback sockets. Component tests use injected clocks, in-memory stores, temporary directories, and mocked external boundaries. Black-box E2E tests run in `tests/e2e` using `redis-cli`, poll for socket readiness rather than relying on fixed sleeps, and assert every command and option listed above, including malformed requests, TTL boundaries, pipelining, concurrency, restart recovery, and exact reply formats. `coverage run -m unittest discover -s tests` followed by `coverage report` must show at least 95% line coverage for `src/`.

## 10. Docker E2E Harness

`docker-compose.e2e.yml` defines `api` and `e2e` services. `api` builds the repository, runs `python3 -m src.main`, sets `PYEDIS_DATA_DIR=/data`, `PORT=6379`, and `PYEDIS_AOF_FSYNC=true`, mounts a named data volume, and exposes port 6379. `e2e` builds from `tests/e2e`, uses Python 3.14 Alpine with redis-cli installed, depends on `api`, receives `REDIS_URL=redis://api:6379`, and runs `/tests/run_tests.sh`. The script exits nonzero on the first failed assertion and zero only when all scenarios pass.

## 11. Documentation

`README.md` documents installation, execution, environment variables, every command and exact reply/error contract, RESP framing, AOF format, persistence behavior, and `make test`, `make lint`, and `make e2e`. `docs/index.md` is the Read the Docs entry point. `docs/api.md` documents commands, RESP, architecture boundaries, expiration, persistence, deployment, and operational diagnostics. `.readthedocs.yaml` builds the `docs/` bundle.

## 12. Global Acceptance

The implementation is complete only when all required files exist, no source file exceeds 500 lines, no pytest artifact exists, `make build`, `make test`, `make lint`, and `make e2e` succeed, redis-cli and redis-py pass all scenarios, restart durability and corrupt trailing-line recovery work, and coverage is at least 95%.