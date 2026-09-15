#!/bin/sh
set -eu
redis-cli -u "${REDIS_URL:-redis://127.0.0.1:6379}" ping | grep -qx PONG
