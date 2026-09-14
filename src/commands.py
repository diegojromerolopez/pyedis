from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from .persistence import AOF
from .resp import bulk, error, integer, simple, array
from .store import Store


class Dispatcher:
    def __init__(self, store: Store, aof: AOF) -> None:
        self.store, self.aof = store, aof
        self.handlers: dict[str, Callable[[list[bytes]], Awaitable[bytes]]] = {
            "PING": self.ping, "ECHO": self.echo, "QUIT": self.quit,
            "SET": self.set, "GET": self.get, "DEL": self.delete,
            "EXISTS": self.exists, "INCR": self.incr, "DECR": self.decr,
            "EXPIRE": self.expire, "TTL": self.ttl, "KEYS": self.keys,
            "FLUSHALL": self.flush,
        }

    def arity(self, name: str, args: list[bytes], minimum: int, maximum: int | None = None) -> bytes | None:
        if len(args) < minimum or (maximum is not None and len(args) > maximum):
            return error(f"ERR wrong number of arguments for '{name.lower()}' command")
        return None

    async def dispatch(self, parts: list[bytes]) -> bytes:
        if not parts:
            return error("ERR syntax error")
        name = parts[0].decode(errors="replace").upper()
        handler = self.handlers.get(name)
        if handler is None:
            return error(f"ERR unknown command '{name}'")
        return await handler(parts[1:])

    async def ping(self, args: list[bytes]) -> bytes:
        bad = self.arity("ping", args, 0, 1)
        return bad or (simple("PONG") if not args else bulk(args[0]))

    async def echo(self, args: list[bytes]) -> bytes:
        bad = self.arity("echo", args, 1, 1)
        return bad or bulk(args[0])

    async def quit(self, args: list[bytes]) -> bytes:
        return self.arity("quit", args, 0, 0) or simple("OK")

    async def set(self, args: list[bytes]) -> bytes:
        if len(args) < 2:
            return error("ERR wrong number of arguments for 'set' command")
        key, value = args[0].decode(), args[1]
        expiry: float | None = None
        nx = xx = False
        i = 2
        try:
            while i < len(args):
                flag = args[i].upper()
                if flag in (b"NX", b"XX"):
                    if flag == b"NX": nx = True
                    else: xx = True
                    i += 1
                elif flag in (b"EX", b"PX") and i + 1 < len(args):
                    amount = int(args[i + 1])
                    if amount <= 0: raise ValueError
                    expiry = self.store.clock() + (amount if flag == b"EX" else amount / 1000)
                    i += 2
                else: raise ValueError
            if nx and xx: raise ValueError
        except ValueError:
            return error("ERR syntax error" if nx and xx else "ERR value is not an integer or out of range")
        ok = await self.store.set(key, value, expiry, nx, xx)
        if ok:
            self.aof.append({"op": "SET", "key": key, "value": value.decode(errors="replace"), "expire_at": expiry})
        return simple("OK") if ok else bulk(None)

    async def get(self, args: list[bytes]) -> bytes:
        bad = self.arity("get", args, 1, 1)
        if bad: return bad
        return bulk(await self.store.get(args[0].decode()))

    async def delete(self, args: list[bytes]) -> bytes:
        bad = self.arity("del", args, 1)
        if bad: return bad
        keys = [x.decode() for x in args]
        count = await self.store.delete(keys)
        for key in keys: self.aof.append({"op": "DEL", "key": key})
        return integer(count)

    async def exists(self, args: list[bytes]) -> bytes:
        bad = self.arity("exists", args, 1)
        if bad: return bad
        return integer(sum(await self.store.exists(x.decode()) for x in args))

    async def incr(self, args: list[bytes]) -> bytes:
        return await self._change("incr", args, 1)

    async def decr(self, args: list[bytes]) -> bytes:
        return await self._change("decr", args, -1)

    async def _change(self, name: str, args: list[bytes], delta: int) -> bytes:
        bad = self.arity(name, args, 1, 1)
        if bad: return bad
        key = args[0].decode()
        try: value = await self.store.increment(key, delta)
        except ValueError: return error("ERR value is not an integer or out of range")
        self.aof.append({"op": name.upper(), "key": key})
        return integer(value)

    async def expire(self, args: list[bytes]) -> bytes:
        bad = self.arity("expire", args, 2, 2)
        if bad: return bad
        try: seconds = int(args[1])
        except ValueError: return error("ERR value is not an integer or out of range")
        result = await self.store.expire(args[0].decode(), seconds)
        if result and seconds > 0: self.aof.append({"op": "EXPIRE", "key": args[0].decode(), "expire_at": self.store.clock() + seconds})
        return integer(int(result))

    async def ttl(self, args: list[bytes]) -> bytes:
        bad = self.arity("ttl", args, 1, 1)
        return bad or integer(await self.store.ttl(args[0].decode()))

    async def keys(self, args: list[bytes]) -> bytes:
        bad = self.arity("keys", args, 1, 1)
        if bad: return bad
        return array([bulk(key) for key in await self.store.keys(args[0].decode())])

    async def flush(self, args: list[bytes]) -> bytes:
        bad = self.arity("flushall", args, 0, 0)
        if bad: return bad
        await self.store.flush(); self.aof.append({"op": "FLUSHALL"}); self.aof.truncate()
        return simple("OK")
