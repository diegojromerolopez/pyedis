#!/bin/bash
set -e

REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

echo "Testing PING..."
PING_OUT=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" PING)
if [ "$PING_OUT" != "PONG" ]; then
  echo "PING test failed: expected PONG, got '$PING_OUT'"
  exit 1
fi

echo "Testing ECHO hello..."
ECHO_OUT=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ECHO hello)
if [ "$ECHO_OUT" != "hello" ]; then
  echo "ECHO test failed: expected hello, got '$ECHO_OUT'"
  exit 1
fi

echo "Testing QUIT..."
QUIT_OUT=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" QUIT)
if [ "$QUIT_OUT" != "OK" ]; then
  echo "QUIT test failed: expected OK, got '$QUIT_OUT'"
  exit 1
fi

echo "All E2E tests passed!"
