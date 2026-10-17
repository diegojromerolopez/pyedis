#!/usr/bin/env bash
set -euo pipefail

HOST="${REDIS_HOST:-127.0.0.1}"
PORT="${REDIS_PORT:-6379}"

echo "Executing E2E tests against ${HOST}:${PORT}..."

# Test PING
res=$(redis-cli -h "$HOST" -p "$PORT" PING)
if [ "$res" != "PONG" ]; then
  echo "E2E Failure: Expected PONG, got $res"
  exit 1
fi

# Test SET & GET
redis-cli -h "$HOST" -p "$PORT" SET testkey testval
res=$(redis-cli -h "$HOST" -p "$PORT" GET testkey)
if [ "$res" != "testval" ]; then
  echo "E2E Failure: Expected testval, got $res"
  exit 1
fi

echo "All E2E tests passed successfully!"
