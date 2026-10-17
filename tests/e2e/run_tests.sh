#!/usr/bin/env bash
set -euo pipefail

HOST="${REDIS_HOST:-127.0.0.1}"
PORT="${REDIS_PORT:-6379}"

echo "Running E2E tests against ${HOST}:${PORT}..."

# PING test
RESP=$(redis-cli -h "$HOST" -p "$PORT" PING)
if [ "$RESP" != "PONG" ]; then
  echo "Expected PONG, got $RESP"
  exit 1
fi

# SET/GET test
redis-cli -h "$HOST" -p "$PORT" SET mykey myvalue
VAL=$(redis-cli -h "$HOST" -p "$PORT" GET mykey)
if [ "$VAL" != "myvalue" ]; then
  echo "Expected myvalue, got $VAL"
  exit 1
fi

echo "E2E tests completed successfully!"
