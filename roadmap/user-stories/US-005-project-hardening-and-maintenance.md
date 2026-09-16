# US-005 — Project Hardening, Maintenance Readiness & Code Quality

**depends_on:** ["US-001", "US-002", "US-003", "US-004"]  
**change_type:** new

## User story
As a maintainer, I want a clean, documented, fully verified repository so that pyedis can be released and operated without hidden regressions.

## Mandatory sequential tasks

1. Repository-wide auto-formatting and import hygiene: run `ruff format src tests`, remove unused imports and prohibited artifacts, and retain behavior with co-located regression checks.
2. Best-effort static analysis: run `ruff check src tests` and `mypy --strict src`, resolve findings without `# noqa` style suppression or hiding typing defects with `# type: ignore`.
3. QA-supervised regression and all-scenario black-box E2E verification: run every unittest, redis-py integration, redis-cli E2E command scenario, fragmentation/pipelining case, concurrency case, restart case, signal case, and configuration error case with socket readiness polling and zero regressions.
4. Packaging, documentation, and executable sanity checks: verify all required paths, manifests, Makefile recipes, Docker Compose files, README/docs links, coverage, and clean install/run/test/lint/e2e behavior.

## Definition of Done (DoD)

- `make format` is idempotent; `make lint` runs exactly `ruff check src tests` and `mypy --strict src`, both with zero findings. No source file exceeds 500 lines.
- `make test` executes `python3 -m unittest discover -s tests -v`, discovers the complete unit and integration suite, and exits nonzero on any failure or on zero tests. All tests pass.
- `make e2e` executes `docker compose -f docker-compose.e2e.yml up --build --exit-code-from e2e` and exits `0`. The E2E suite physically runs separate scenarios for PING, ECHO, QUIT, SET, GET, DEL, EXISTS, INCR, DECR, EXPIRE, TTL, KEYS, FLUSHALL, unknown commands, inline input, pipelining, binary values, concurrency, restart, AOF corruption, and configuration behavior, asserting exact payloads and formatting.
- Coverage is measured with the permitted `coverage` tool and is at least 95% across `src/`; coverage-only tests are not accepted as a substitute for behavior tests.
- Every external boundary is dependency-injected in unit tests; deterministic fake clocks cover all expiration assertions. Live sockets and redis-cli/redis-py are used only in integration/E2E acceptance tests.
- Required paths are present: `pyproject.toml`, `requirements.txt`, `Makefile`, `README.md`, `.readthedocs.yaml`, `.gitignore`, `docker-compose.yml`, `docker-compose.e2e.yml`, `docs/index.md`, `docs/api.md`, `src/__init__.py`, `src/main.py`, `src/resp.py`, `src/store.py`, `src/commands.py`, `src/persistence.py`, all specified test files, and `data/` runtime behavior.
- No pytest dependency, import, configuration, artifact, or invocation exists. No external web framework is used. No stubs, placeholders, ignored failures, `set +e`, `|| true`, or tautological assertions exist. Diagnostics retain the `pyedis: ` prefix and protocol/error envelopes remain exact.
- The thin primary entrypoint remains under 15 lines and delegates to a testable lifecycle function. Clean signals exit `0`; fatal startup errors exit `1`.

```noctifab-contract
{"story_id": "US-005","public_contracts":[{"id":"release.quality-gates","interface":"Makefile build/test/lint/format/e2e and Docker Compose black-box server","applicable_path_prefixes":["Makefile","src/","tests/","docs/","docker-compose.e2e.yml","pyproject.toml"],"allowed_executables":["make test","make lint","make format","make e2e","python3 -m src.main"],"exit_codes":[0,1],"stdout_contains":[],"stderr_prefixes":["pyedis: "]}]}
```