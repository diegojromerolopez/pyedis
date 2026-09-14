#!/bin/sh
set -eu
host="${REDIS_URL#redis://}"
redis-cli -h "${host%:*}" -p "${host##*:}" ping | grep -qx PONG
redis-cli -h "${host%:*}" -p "${host##*:}" set e2e-key value | grep -qx OK
redis-cli -h "${host%:*}" -p "${host##*:}" get e2e-key | grep -qx value
redis-cli -h "${host%:*}" -p "${host##*:}" flushall | grep -qx OK
