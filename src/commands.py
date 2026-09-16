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
            if len(values) > 1:
                return self._arity("ping"), False
            return (simple("PONG") if not values else bulk(values[0])), False
        if name == "ECHO":
            if len(values) != 1:
                return self._arity("echo"), False
            return bulk(values[0]), False
        if name == "QUIT":
            if values:
                return self._arity("quit"), False
            return simple("OK"), True
        if name == "SET":
            if len(values) < 2:
                return self._arity("set"), False
            key = values[0].decode()
            value = values[1]
            nx = False
            xx = False
            expire_at: float | None = None
            i = 2
            while i < len(values):
                flag = values[i].decode(errors="replace").upper()
                if flag == "NX":
                    nx = True
                    i += 1
                elif flag == "XX":
                    xx = True
                    i += 1
                elif flag == "EX":
                    if i + 1 >= len(values):
                        return error("ERR syntax error"), False
                    try:
                        seconds = int(values[i + 1])
                    except ValueError:
                        return error(
                            "ERR value is not an integer or out of range"
                        ), False
                    if seconds <= 0:
                        return error(
                            "ERR value is not an integer or out of range"
                        ), False
                    expire_at = self.store.clock() + seconds
                    i += 2
                elif flag == "PX":
                    if i + 1 >= len(values):
                        return error("ERR syntax error"), False
                    try:
                        ms = int(values[i + 1])
                    except ValueError:
                        return error(
                            "ERR value is not an integer or out of range"
                        ), False
                    if ms <= 0:
                        return error(
                            "ERR value is not an integer or out of range"
                        ), False
                    expire_at = self.store.clock() + ms / 1000.0
                    i += 2
                else:
                    return error("ERR syntax error"), False
            if nx and xx:
                return error("ERR syntax error"), False
            result = await self.store.set(key, value, expire_at, nx=nx, xx=xx)
            if not result:
                return bulk(None), False
            self.aof.append(
                {
                    "op": "SET",
                    "key": key,
                    "value": value.decode(errors="replace"),
                    "expire_at": expire_at,
                }
            )
            return simple("OK"), False
        if name == "GET":
            if len(values) != 1:
                return self._arity("get"), False
            return bulk(await self.store.get(values[0].decode())), False
        if name == "DEL":
            if not values:
                return self._arity("del"), False
            keys = [v.decode() for v in values]
            count = await self.store.delete(keys)
            if count > 0:
                for key in keys:
                    self.aof.append({"op": "DEL", "key": key})
            return integer(count), False
        if name == "EXISTS":
            if not values:
                return self._arity("exists"), False
            count = sum(await self.store.exists(v.decode()) for v in values)
            return integer(count), False
        if name in ("INCR", "DECR"):
            if len(values) != 1:
                return self._arity(name.lower()), False
            key = values[0].decode()
            try:
                result = await self.store.number(key, 1 if name == "INCR" else -1)
            except ValueError:
                return error("ERR value is not an integer or out of range"), False
            self.aof.append({"op": name, "key": key})
            return integer(result), False
        if name == "TTL":
            if len(values) != 1:
                return self._arity("ttl"), False
            return integer(await self.store.ttl(values[0].decode())), False
        if name == "EXPIRE":
            if len(values) != 2:
                return self._arity("expire"), False
            try:
                seconds = int(values[1])
            except ValueError:
                return error("ERR value is not an integer or out of range"), False
            key = values[0].decode()
            result = await self.store.expire(key, seconds)
            if result:
                self.aof.append(
                    {
                        "op": "EXPIRE",
                        "key": key,
                        "expire_at": self.store.clock() + seconds,
                    }
                )
            return integer(int(result)), False
        if name == "KEYS":
            if len(values) != 1:
                return self._arity("keys"), False
            return array(await self.store.keys(values[0].decode())), False
        if name == "FLUSHALL":
            if values:
                return self._arity("flushall"), False
            await self.store.flush()
            self.aof.truncate()
            return simple("OK"), False
        if name == "COMMAND":
            return array([]), False
        return error(f"ERR unknown command '{args[0].decode(errors='replace')}'"), False

    @staticmethod
    def _arity(command: str) -> bytes:
        return error(f"ERR wrong number of arguments for '{command}' command")
