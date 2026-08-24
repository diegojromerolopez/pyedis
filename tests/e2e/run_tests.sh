#!/usr/bin/env bash
set -euo pipefail

HOST="${REDIS_HOST:-127.0.0.1}"
PORT="${REDIS_PORT:-6379}"

cli() {
    if command -v redis-cli &>/dev/null; then
        redis-cli -h "$HOST" -p "$PORT" "$@"
    else
        python3 -c "
import socket, sys
s = socket.socket()
s.connect(('$HOST', int('$PORT')))
cmd = sys.argv[1:]
resp = '*' + str(len(cmd)) + '\r\n'
for arg in cmd:
    b_arg = arg.encode('utf-8')
    resp += '$' + str(len(b_arg)) + '\r\n' + arg + '\r\n'
s.sendall(resp.encode('utf-8'))
out = s.recv(4096).decode('utf-8', errors='replace')
sys.stdout.write(out)
s.close()
" "$@"
    fi
}

echo "Testing SET..."
res=$(cli SET e2e_key e2e_val)
echo "SET response: $res"

echo "Testing GET..."
res=$(cli GET e2e_key)
echo "GET response: $res"

echo "Testing EXISTS..."
res=$(cli EXISTS e2e_key non_existent_key)
echo "EXISTS response: $res"

echo "Testing DEL..."
res=$(cli DEL e2e_key)
echo "DEL response: $res"

echo "Testing GET after DEL..."
res=$(cli GET e2e_key)
echo "GET after DEL response: $res"

echo "E2E tests passed successfully!"
