"""Command execution."""
from __future__ import annotations

import time
from typing import Any
from .resp import encode
from .store import Store
from .persistence import AOF

class Commands:
    def __init__(self, store: Store, aof: AOF) -> None:
        self.store, self.aof = store, aof

    def run(self, argv: list[bytes]) -> tuple[bytes, bool]:
        if not argv:
            return b"-ERR empty command\r\n", False
        name = argv[0].decode(errors='replace').upper(); args = argv[1:]
        if name == 'PING':
            return (encode(args[0]) if len(args) == 1 else encode('PONG')) if len(args) <= 1 else (b"-ERR wrong number of arguments for 'ping' command\r\n", False)
        if name == 'ECHO':
            return (encode(args[0]), False) if len(args) == 1 else (b"-ERR wrong number of arguments for 'echo' command\r\n", False)
        if name == 'QUIT':
            return (b'+OK\r\n', True) if not args else (b"-ERR wrong number of arguments for 'quit' command\r\n", False)
        if name == 'GET':
            return (encode(self.store.get(args[0])), False) if len(args) == 1 else (b"-ERR wrong number of arguments for 'get' command\r\n", False)
        if name == 'SET':
            if len(args) < 2: return b"-ERR syntax error\r\n", False
            expiry = None; i = 2
            while i < len(args):
                option = args[i].upper()
                if option in (b'EX', b'PX') and i + 1 < len(args):
                    try: number = int(args[i + 1]); expiry = time.time() + number * (1 if option == b'EX' else .001)
                    except ValueError: return b"-ERR value is not an integer or out of range\r\n", False
                    i += 2
                else: return b"-ERR syntax error\r\n", False
            self.store.set(args[0], args[1], expiry); self.aof.append({'op':'SET','key':args[0].decode(),'value':args[1].decode(),'expire_at':expiry})
            return b'+OK\r\n', False
        if name in ('DEL', 'EXISTS'):
            if not args: return f"-ERR wrong number of arguments for '{name.lower()}' command\r\n".encode(), False
            count = sum((self.store.delete(k) if name == 'DEL' else self.store.get(k) is not None) for k in args)
            if name == 'DEL' and count: self.aof.append({'op':'DEL','key':args[0].decode()})
            return encode(count), False
        if name == 'KEYS':
            return encode(self.store.keys(args[0] if args else b'*')), False
        if name == 'FLUSHALL':
            if args: return b"-ERR wrong number of arguments for 'flushall' command\r\n", False
            self.store.clear(); self.aof.append({'op':'FLUSHALL'}); self.aof.truncate(); return b'+OK\r\n', False
        return f"-ERR unknown command '{name}'\r\n".encode(), False
