from __future__ import annotations

import time
from .persistence import AOF
from .resp import array, bulk, error, integer, simple
from .store import Store


class Dispatcher:
    def __init__(self, store: Store, aof: AOF) -> None:
        self.store = store
        self.aof = aof

    def _arity(
        self, command: str, args: list[bytes], minimum: int, maximum: int | None = None
    ) -> bytes | None:
        if len(args) < minimum or maximum is not None and len(args) > maximum:
            return error(f"ERR wrong number of arguments for '{command.lower()}' command")
        return None

    async def dispatch(self, parts: list[bytes]) -> tuple[bytes, bool]:
        if not parts:
            return b"", False
        command = parts[0].decode(errors="replace").upper()
        args = parts[1:]
        name = command.lower()
        if command == "PING":
            bad = self._arity(name, args, 0, 1)
            return (bad or (simple("PONG") if not args else bulk(args[0]))), False
        if command == "ECHO":
            bad = self._arity(name, args, 1, 1)
            return (bad or bulk(args[0])), False
        if command == "QUIT":
            bad = self._arity(name, args, 0, 0)
            return (bad or simple("OK")), True
        if command == "SET":
            if len(args) < 2:
                return error("ERR wrong number of arguments for 'set' command"), False
            key, value = args[0].decode(), args[1]
            nx = xx = False
            expiry: float | None = None
            i = 2
            try:
                while i < len(args):
                    flag = args[i].upper()
                    if flag == b"NX":
                        nx = True
                    elif flag == b"XX":
                        xx = True
                    elif flag in (b"EX", b"PX"):
                        i += 1
                        duration = int(args[i])
                        if duration <= 0:
                            raise ValueError
                        expiry = time.time() + (duration if flag == b"EX" else duration / 1000)
                    else:
                        raise ValueError
                    i += 1
            except (ValueError, IndexError):
                return error("ERR value is not an integer or out of range"), False
            if nx and xx:
                return error("ERR syntax error"), False
            present = await self.store.exists(key)
            if nx and present or xx and not present:
                return bulk(None), False
            await self.store.set(key, value, expiry)
            self.aof.append(
                {
                    "op": "SET",
                    "key": key,
                    "value": value.decode(errors="replace"),
                    "expire_at": expiry,
                }
            )
            return simple("OK"), False
        if command == "GET":
            bad = self._arity(name, args, 1, 1)
            if bad:
                return bad, False
            return bulk(await self.store.get(args[0].decode())), False
        if command in ("DEL", "EXISTS"):
            bad = self._arity(name, args, 1)
            if bad:
                return bad, False
            keys = [x.decode() for x in args]
            if command == "DEL":
                count = await self.store.delete(keys)
                if count:
                    self.aof.append({"op": "DEL", "key": keys[0]})
            else:
                count = sum(await self.store.exists(key) for key in keys)
            return integer(count), False
        if command in ("INCR", "DECR"):
            bad = self._arity(name, args, 1, 1)
            if bad:
                return bad, False
            try:
                value = await self.store.increment(args[0].decode(), 1 if command == "INCR" else -1)
            except ValueError:
                return error("ERR value is not an integer or out of range"), False
            self.aof.append({"op": command, "key": args[0].decode()})
            return integer(value), False
        if command == "EXPIRE":
            bad = self._arity(name, args, 2, 2)
            if bad:
                return bad, False
            try:
                seconds = int(args[1])
            except ValueError:
                return error("ERR value is not an integer or out of range"), False
            result = await self.store.expire(args[0].decode(), seconds)
            if result and seconds > 0:
                self.aof.append(
                    {"op": "EXPIRE", "key": args[0].decode(), "expire_at": time.time() + seconds}
                )
            return integer(int(result)), False
        if command == "TTL":
            bad = self._arity(name, args, 1, 1)
            return (bad or integer(await self.store.ttl(args[0].decode()))), False
        if command == "KEYS":
            bad = self._arity(name, args, 1, 1)
            if bad:
                return bad, False
            return array([bulk(key) for key in await self.store.keys(args[0].decode())]), False
        if command == "FLUSHALL":
            bad = self._arity(name, args, 0, 0)
            if bad:
                return bad, False
            await self.store.flush()
            self.aof.append({"op": "FLUSHALL"})
            self.aof.truncate()
            return simple("OK"), False
        return error(f"ERR unknown command '{command}'"), False
