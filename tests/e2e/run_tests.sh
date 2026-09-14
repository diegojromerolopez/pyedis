#!/bin/bash
set -e

REDIS_HOST=$(echo ${REDIS_URL} | sed -e 's/redis:\/\///' -e 's/:.*//')
REDIS_PORT=$(echo ${REDIS_URL} | sed -e 's/.*://')

if [ -z "$REDIS_HOST" ]; then REDIS_HOST="api"; fi
if [ -z "$REDIS_PORT" ]; then REDIS_PORT="6379"; fi

cli="redis-cli -h $REDIS_HOST -p $REDIS_PORT"

res=$($cli ping)
if [ "$res" != "PONG" ]; then echo "PING failed"; exit 1; fi

res=$($cli set k1 v1)
if [ "$res" != "OK" ]; then echo "SET failed"; exit 1; fi

res=$($cli get k1)
if [ "$res" != "v1" ]; then echo "GET failed"; exit 1; fi

echo "E2E tests passed successfully."
