# US-002 — Walking Skeleton & Scaffolding

**change_type:** new  
**depends_on:** []

## User Story
As an operator, I want a minimal pyedis process that starts, accepts a TCP connection, and answers PING so that the repository is runnable before deeper protocol, storage, and persistence work begins.

## Requirements and Atomic Tasks

1. Create the thin executable entrypoint `src/main.py`, package marker `src/__init__.py`, `pyproject.toml`, `requirements.txt`, root `Makefile`, and `.gitignore`. The first implementation must be a real asyncio TCP daemon with a health-only PING path, not a stub. Add a co-located `tests/integration/test_server.py` unittest smoke test that polls socket readiness and asserts `+PONG\r\n`.
2. Add the initial `README.md`, `docs/index.md`, `docs/api.md`, `.readthedocs.yaml`, and minimal `docker-compose.yml`/e2e harness wiring so the server can be run, documented, and container-built. The skeleton may expose only PING, but must preserve the final required paths and use `python3 -m unittest discover -s tests -v`.

## Definition of Done (DoD)

- Observable entrypoints are `python3 -m src.main`, `make run`, and a TCP listener on `PORT` default 6379. A RESP array containing `PING` returns exactly `+PONG\r\n`; inline `PING\r\n` returns the same. Malformed startup configuration or bind failure writes `pyedis: <reason>` to stderr and exits 1.
- `src/main.py` is a thin wrapper under 15 lines delegating immediately to a testable server function. No `pass`, ellipsis, `NotImplementedError`, placeholder response, tautological assertion, shell masking, or fake-only implementation is allowed.
- Exact required paths are present: `pyproject.toml`, `requirements.txt`, `Makefile`, `README.md`, `.readthedocs.yaml`, `docs/index.md`, `docs/api.md`, `.gitignore`, `docker-compose.yml`, `src/__init__.py`, `src/main.py`, and `tests/integration/test_server.py`.
- `make test` runs only `python3 -m unittest discover -s tests -v`, exits nonzero on failure or zero tests, and imports no pytest artifact. `pytest`, third-party test frameworks, `conftest.py`, `pytest.ini`, and `docker-compose` hyphenated commands are forbidden.
- The smoke test is Chicago-school and black-box: it starts the real server boundary, polls readiness, sends a real RESP/inline PING, and asserts the exact bytes. Intermediate tests use injected/fake streams where appropriate; no fixed sleep is used.
- Edge cases covered include mixed-case PING, fragmented request bytes, a pipelined pair of PING requests, connection close, invalid port configuration, and port binding failure. Every scenario asserts observable bytes and exit behavior rather than merely importing modules.
- The repository contains no required external runtime framework, uses Python 3.10+ annotations with built-in generic collections, and all functions have annotations. Linting may be advisory in this story, but no pytest dependency or invocation may exist.
- Contract verification has 100% passing unittest and skeleton black-box scenarios. Full command coverage belongs to later stories and the final hardening story.

```noctifab-contract
{
  "story_id": "US-002",
  "public_contracts": [
    {
      "id": "resp.ping",
      "interface": "TCP RESP2 or inline command on PORT",
      "applicable_path_prefixes": ["src/", "tests/", "Makefile"],
      "allowed_executables": ["python3 -m src.main", "make run"],
      "exit_codes": [0, 1],
      "stdout_contains": [],
      "stderr_prefixes": ["pyedis: "]
    }
  ]
}
```

## Refined Acceptance Criteria & Missing Requirements

The QA Acceptance Review identified the following incomplete features and requirements that MUST be implemented to satisfy the Definition of Done:

- [ ] **Missing Feature**: Fix client_session exception handling to inspect the caught exception via an `as exc` binding rather than the undefined `_` variable.
- [ ] **Missing Feature**: Ensure clean client connection closure and incomplete requests terminate without an internal NameError and satisfy the required observable exit/connection behavior.
- [ ] **Missing Feature**: Ensure malformed protocol requests return the intended RESP error response rather than failing inside the exception handler.
- [ ] **Missing Feature**: Verify that the authoritative src/server.py contains only a syntactically valid `async def client_session`; the supplied source shows a non-async definition containing await expressions.
- [ ] **Missing Feature**: Re-run the full unittest discovery and black-box scenarios after these fixes, including mixed-case PING, fragmented requests, pipelined PINGs, connection close, invalid PORT configuration, and bind failure.

**Audit Summary**: The walking skeleton is not fully compliant. Although the repository appears to contain most required scaffolding and implements the intended asyncio RESP/inline PING path, the server session error-handling code is defective: it references the undefined variable '_' when handling IncompleteReadError or protocol errors. This causes connection-close and malformed-request scenarios to raise NameError instead of producing the required observable behavior. The supplied source also shows a client_session definition containing await expressions without an async declaration, which would make the module invalid if that version is authoritative. Consequently, the required connection-close, malformed-input, and complete black-box behavior cannot be accepted as implemented.
