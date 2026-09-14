#!/bin/sh
set -eu
host="${REDIS_URL#redis://}"
host="${host%%:*}"
port="${REDIS_URL##*:}"
[ "$(redis-cli -h "$host" -p "$port" ping)" = PONG ]
[ "$(redis-cli -h "$host" -p "$port" set k v)" = OK ]
[ "$(redis-cli -h "$host" -p "$port" get k)" = v ]
[ "$(redis-cli -h "$host" -p "$port" incr n)" = 1 ]
[ "$(redis-cli -h "$host" -p "$port" flushall)" = OK ]
