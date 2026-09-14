#!/usr/bin/env bash
set -euo pipefail

REDIS_URL=${REDIS_URL:-redis://127.0.0.1:6379}
HOST=$(echo $REDIS_URL | sed -e 's,redis://,,' | cut -d: -f1)
PORT=$(echo $REDIS_URL | sed -e 's,redis://,,' | cut -d: -f2)

CLI="redis-cli -h $HOST -p $PORT"

echo "Running pyedis E2E assertions against $HOST:$PORT..."

res=$($CLI ping)
if [ "$res" != "PONG" ]; then echo "FAIL: PING ($res)"; exit 1; fi

res=$($CLI ping "hello world")
if [ "$res" != "hello world" ]; then echo "FAIL: PING msg ($res)"; exit 1; fi

res=$($CLI set k1 v1)
if [ "$res" != "OK" ]; then echo "FAIL: SET ($res)"; exit 1; fi

res=$($CLI get k1)
if [ "$res" != "v1" ]; then echo "FAIL: GET ($res)"; exit 1; fi

res=$($CLI incr counter)
if [ "$res" != "1" ]; then echo "FAIL: INCR ($res)"; exit 1; fi

res=$($CLI flushall)
if [ "$res" != "OK" ]; then echo "FAIL: FLUSHALL ($res)"; exit 1; fi

echo "All E2E black-box assertions PASSED!"
exit 0
