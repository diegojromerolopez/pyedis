# US-001 — Walking Skeleton TCP Server and Project Scaffolding

**depends_on:** []  
**change_type:** new

## User Story

As an operator, I want a runnable pyedis TCP process with a minimal RESP/inline PING health path so that the project can be built, started, tested, and extended safely.

## Requirements

1. Create the required manifests and entrypoint: `pyproject.toml`, `requirements.txt`, `Makefile`, `src/__init__.py`, `src/main.py`, and the initial `tests/integration/test_server.py`.
2. Implement a thin `python3 -m src.main` entrypoint that starts an asyncio TCP listener on `PORT`, supports `PING` and `PING message` over both RESP arrays and inline CRLF commands, and handles clean SIGINT/SIGTERM shutdown.
3. Provide exact replies `+PONG\r\n` and bulk-string echo replies. Invalid PING arity returns `-ERR wrong number of arguments for 'ping' command\r\n`.
4. Include `make build`, `make install`, `make run`, `make test`, `make lint`, `make format`, and `make e2e` recipes without pytest or hyphenated docker-compose commands.

## Definition of Done (DoD)

- **Observable contract:** `python3 -m src.main` listens on `127.0.0.1:${PORT}`; RESP `*1\\r\\n$4\\r\\nPING\\r\\n` returns `+PONG\\r\\n`; inline `PING hello\\r\\n` returns `$5\\r\\nhello\\r\\n`; malformed PING arity returns the exact error above.
- **Lifecycle:** startup failure writes `pyedis: <reason>` to stderr and exits 1; SIGINT/SIGTERM closes the listener and exits 0. Diagnostics use the `pyedis: ` prefix.
- **Testing:** use Chicago-school `unittest.IsolatedAsyncioTestCase`, injected/testable server boundaries, and real observable socket replies. E2E must poll socket readiness and execute separate black-box scenarios for PING, PING with a message, inline framing, RESP framing, and invalid arity.
- **Anti-stub:** no `pass`, ellipsis placeholders, `NotImplementedError`, tautological assertions, shell error masking, or empty test suites.
- **Required paths:** `pyproject.toml`, `requirements.txt`, `Makefile`, `src/__init__.py`, `src/main.py`, and `tests/integration/test_server.py` must exist. The thin primary wrapper delegates immediately to a testable core and remains under 15 lines where practical.
- **Forbidden tools:** pytest and all third-party test frameworks are forbidden; tests execute through `python3 -m unittest discover -s tests -v`. Runtime code uses only the standard library.
- **Verification:** all implemented unit/integration/E2E tests pass with zero failures. Lint is advisory in this intermediate story.

```noctifab-contract
{"story_id": "US-001","public_contracts":[{"id":"server.ping","interface":"TCP RESP2/inline server via python3 -m src.main","applicable_path_prefixes":["src/","tests/"],"allowed_executables":["python3 -m src.main"],"exit_codes":[0,1],"stdout_contains":[],"stderr_prefixes":["pyedis: "]}]}
```