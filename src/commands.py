"""Redis command dispatcher."""
from __future__ import annotations

from .persistence import AOF
from .resp import bulk, error, integer, simple, array
from .store import Store


class Dispatcher:
    def __init__(self, store: Store, aof: AOF | None = None) -> None:
        self.store = store
        self.aof = aof

    async def execute(self, parts: list[bytes]) -> tuple[bytes, bool]:
        if not parts:
            return error("ERR empty command"), False
        name = parts[0].decode(errors="replace").upper()
        args = [part.decode(errors="surrogateescape") for part in parts[1:]]
        expected: dict[str, int | None] = {"PING": None, "ECHO": 1, "QUIT": 0, "SET": None, "GET": 1, "DEL": None, "EXISTS": None, "INCR": 1, "DECR": 1, "EXPIRE": 2, "TTL": 1, "KEYS": 1, "FLUSHALL": 0}
        if name not in expected:
            return error(f"ERR unknown command '{name}'"), False
        arity = expected[name]
        if (arity is not None and len(args) != arity) or (name in {"DEL", "EXISTS"} and not args) or (name == "SET" and len(args) < 2) or (name == "PING" and len(args) > 1):
            return error(f"ERR wrong number of arguments for '{name.lower()}' command"), False
        if name == "PING": return (simple("PONG") if not args else bulk(parts[1])), False
        if name == "ECHO": return bulk(parts[1]), False
        if name == "QUIT": return simple("OK"), True
        if name == "GET": return bulk(await self.store.get(args[0])), False
        if name in {"DEL", "EXISTS"}:
            value = await (self.store.delete(args) if name == "DEL" else self._exists(args))
            if name == "DEL" and self.aof:
                for key in args: self.aof.append({"op": "DEL", "key": key})
            return integer(value), False
        if name in {"INCR", "DECR"}:
            result = await self.store.incr(args[0], 1 if name == "INCR" else -1)
            if result is None: return error("ERR value is not an integer or out of range"), False
            if self.aof: self.aof.append({"op": name, "key": args[0]})
            return integer(result[0]), False
        if name == "SET": return await self._set(args), False
        if name == "EXPIRE": return await self._expire(args), False
        if name == "TTL": return integer(await self.store.ttl(args[0])), False
        if name == "KEYS": return array(await self.store.keys(args[0])), False
        await self.store.flush()
        if self.aof: self.aof.append({"op": "FLUSHALL"}); self.aof.truncate()
        return simple("OK"), False

    async def _exists(self, keys: list[str]) -> int:
        return sum(1 for key in keys if await self.store.exists(key))

    async def _set(self, args: list[str]) -> bytes:
        expire_at = None; nx = False; xx = False; index = 2
        while index < len(args):
            flag = args[index].upper()
            if flag in {"NX", "XX"}:
                nx = nx or flag == "NX"; xx = xx or flag == "XX"; index += 1
            elif flag in {"EX", "PX"} and index + 1 < len(args):
                try: duration = int(args[index + 1])
                except ValueError: return error("ERR value is not an integer or out of range")
                if duration <= 0: return error("ERR value is not an integer or out of range")
                expire_at = self.store.clock() + duration * (0.001 if flag == "PX" else 1); index += 2
            else: return error("ERR syntax error")
        if nx and xx: return error("ERR syntax error")
        ok = await self.store.set(args[0], args[1], expire_at, nx, xx)
        if ok and self.aof: self.aof.append({"op": "SET", "key": args[0], "value": args[1], "expire_at": expire_at})
        return simple("OK") if ok else bulk(None)

    async def _expire(self, args: list[str]) -> bytes:
        try: seconds = int(args[1])
        except ValueError: return error("ERR value is not an integer or out of range")
        ok = await self.store.expire(args[0], seconds)
        if ok and self.aof: self.aof.append({"op": "EXPIRE", "key": args[0], "expire_at": self.store.clock() + seconds})
        return integer(int(ok))
