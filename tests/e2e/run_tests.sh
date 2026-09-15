#!/bin/sh
set -eu
redis-cli -h "${REDIS_URL#redis://}" ping | grep -q PONG
