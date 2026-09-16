from __future__ import annotations

from src.persistence import AOF
from src.resp import array, bulk, error, integer, simple
from src.store import Store


class Dispatcher:
    def __init__(self, store: Store, aof: AOF) -> None:
        self.store = store
        self.aof = aof

    async def execute(self, args: list[bytes]) -> tuple[bytes, bool]:
        if not args:
            return error("ERR empty command"), False
        name = args[0].decode(errors="replace").upper()
        values = args[1:]
        if name == "PING":
            if len(values) > 1: return self._arity("ping"), False
            return (simple("PONG") if not values else bulk(values[0])), False
        if name == "ECHO":
            if len(values) != 1: return self._arity("echo"), False
            return bulk(values[0]), False
        if name == "QUIT":
            if values: return self._arity("quit"), False
            return simple("OK"), True
        if name == "GET":
            if len(values) != 1: return self._arity("get"), False
            return bulk(await self.store.get(values[0].decode())), False
        if name in ("DEL", "EXISTS"):
            if not values: return self._arity(name.lower()), False
            keys = [v.decode() for v in values]
            result = await self.store.delete(keys) if name == "DEL" else sum(await self.store.exists(k) for k in keys)
            if name == "DEL":
                for key in keys: self.aof.append({"op": "DEL", "key": key})
            return integer(int(result)), False
        if name in ("INCR", "DECR"):
            if len(values) != 1: return self._arity(name.lower()), False
            key = values[0].decode()
            try: result = await self.store.number(key, 1 if name == "INCR" else -1)
            except ValueError: return error("ERR value is not an integer or out of range"), False
            self.aof.append({"op": name, "key": key})
            return integer(result), False
        if name == "TTL":
            if len(values) != 1: return self._arity("ttl"), False
            return integer(await self.store.ttl(values[0].decode())), False
        if name == "EXPIRE":
            if len(values) != 2: return self._arity("expire"), False
            try: seconds = int(values[1])
            except ValueError: return error("ERR value is not an integer or out of range"), False
            key = values[0].decode(); result = await self.store.expire(key, seconds)
            if result: self.aof.append({"op": "EXPIRE", "key": key, "expire_at": self.store.clock() + seconds})
            return integer(int(result)), False
        if name == "KEYS":
            if len(values) != 1: return self._arity("keys"), False
            return array(await self.store.keys(values[0].decode())), False
        if name == "FLUSHALL":
            if values: return self._arity("flushall"), False
            await self.store.flush(); self.aof.append({"op": "FLUSHALL"}); self.aof.truncate()
            return simple("OK"), False
        if name == "COMMAND": return array([]), False
        return error(f"ERR unknown command '{args[0].decode(errors='replace')}'"), False

    @staticmethod
    def _arity(command: str) -> bytes:
        return error(f"ERR wrong number of arguments for '{command}' command")
