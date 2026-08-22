#!/usr/bin/env bash
set -euo pipefail

REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${REDIS_PORT:-6379}"

CLI="redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT}"

echo "=========================================="
echo " Running pyedis E2E Black-Box Test Suite"
echo " Target: ${REDIS_HOST}:${REDIS_PORT}"
echo "=========================================="

# Helper assertion function
assert_eq() {
    local cmd="$1"
    local expected="$2"
    local actual
    actual=$(eval "${CLI} ${cmd}" 2>&1 || true)
    if [ "${actual}" != "${expected}" ]; then
        echo "❌ FAILED: ${cmd}"
        echo "   Expected: '${expected}'"
        echo "   Actual:   '${actual}'"
        exit 1
    else
        echo "✅ PASSED: ${cmd} -> ${actual}"
    fi
}

assert_contains() {
    local cmd="$1"
    local expected="$2"
    local actual
    actual=$(eval "${CLI} ${cmd}" 2>&1 || true)
    if [[ "${actual}" != *"${expected}"* ]]; then
        echo "❌ FAILED: ${cmd}"
        echo "   Expected to contain: '${expected}'"
        echo "   Actual:              '${actual}'"
        exit 1
    else
        echo "✅ PASSED: ${cmd} contains '${expected}'"
    fi
}

echo ""
echo "--- 1. Connection & Liveness Tests ---"
assert_eq "ping" "PONG"
assert_eq "ping 'hello world'" "hello world"
assert_eq "echo 'hello pyedis'" "hello pyedis"

echo ""
echo "--- 2. Basic Key-Value Operations ---"
assert_eq "flushall" "OK"
assert_eq "set k1 v1" "OK"
assert_eq "get k1" "v1"
assert_eq "get non_existent_key" ""

echo ""
echo "--- 3. SET NX / XX Conditional Semantics ---"
assert_eq "set k2 v2 NX" "OK"
assert_eq "set k2 v2_new NX" ""
assert_eq "get k2" "v2"
assert_eq "set k_missing v XX" ""
assert_eq "set k2 v2_updated XX" "OK"
assert_eq "get k2" "v2_updated"

echo ""
echo "--- 4. Expiration & TTL Semantics ---"
assert_eq "set k_exp v_exp EX 1" "OK"
assert_eq "get k_exp" "v_exp"
assert_eq "ttl k_exp" "1"
echo "Waiting 2 seconds for key to expire..."
sleep 2
assert_eq "get k_exp" ""
assert_eq "ttl k_exp" "-2"

assert_eq "set k_persist v_persist" "OK"
assert_eq "ttl k_persist" "-1"
assert_eq "expire k_persist 100" "1"
assert_eq "expire missing_key 10" "0"

echo ""
echo "--- 5. Increment & Decrement Operations ---"
assert_eq "incr counter" "1"
assert_eq "incr counter" "2"
assert_eq "decr counter" "1"
assert_eq "get counter" "1"

echo ""
echo "--- 6. Multi-Key Operations (EXISTS, DEL, KEYS) ---"
assert_eq "set a 1" "OK"
assert_eq "set b 2" "OK"
assert_eq "set c 3" "OK"
assert_eq "exists a" "1"
assert_eq "exists a b missing" "2"
assert_eq "exists a a" "2"
assert_contains "keys '*'" "a"
assert_contains "keys '*'" "b"
assert_contains "keys '*'" "c"
assert_eq "del a b missing" "2"
assert_eq "exists a" "0"
assert_eq "exists b" "0"
assert_eq "exists c" "1"

echo ""
echo "--- 7. Case-Insensitivity Verification ---"
assert_eq "PING" "PONG"
assert_eq "Ping" "PONG"
assert_eq "sEt case_test 42" "OK"
assert_eq "gEt case_test" "42"
assert_eq "dEl case_test" "1"

echo ""
echo "--- 8. Cleanup & Final Verification ---"
assert_eq "flushall" "OK"
assert_eq "keys '*'" ""

echo ""
echo "=========================================="
echo "🎉 ALL E2E BLACK-BOX TESTS PASSED!"
echo "=========================================="
