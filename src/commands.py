from __future__ import annotations

from .persistence import AOF
from .store import Store


def simple(value: str) -> bytes:
    return f"+{value}\r\n".encode()


def error(value: str) -> bytes:
    return f"-ERR {value}\r\n".encode()


def bulk(value: str | bytes | None) -> bytes:
    if value is None:
        return b"$-1\r\n"
    raw = value.encode() if isinstance(value, str) else value
    return b"$" + str(len(raw)).encode() + b"\r\n" + raw + b"\r\n"


class Dispatcher:
    def __init__(self, store: Store, aof: AOF | None = None) -> None:
        self.store = store
        self.aof = aof

    async def dispatch(self, parts: list[bytes]) -> tuple[bytes, bool]:
        if not parts:
            return error("syntax error"), False
        command = parts[0].decode(errors="replace").upper()
        args = [item.decode(errors="replace") for item in parts[1:]]
        if command == "PING":
            if len(args) > 1:
                return error("wrong number of arguments for 'ping' command"), False
            return (simple("PONG") if not args else bulk(args[0])), False
        if command == "ECHO":
            return (bulk(args[0]) if len(args) == 1 else error("wrong number of arguments for 'echo' command")), False
        if command == "QUIT":
            return (simple("OK") if not args else error("wrong number of arguments for 'quit' command")), True
        if command == "GET":
            return (bulk(await self.store.get(args[0])) if len(args) == 1 else error("wrong number of arguments for 'get' command")), False
        if command == "SET":
            if len(args) < 2:
                return error("wrong number of arguments for 'set' command"), False
            key, value = args[:2]
            upper = [item.upper() for item in args[2:]]
            if "NX" in upper and "XX" in upper:
                return error("syntax error"), False
            exists = await self.store.exists(key)
            if ("NX" in upper and exists) or ("XX" in upper and not exists):
                return bulk(None), False
            expiry = None
            index = 0
            while index < len(upper):
                if upper[index] in {"EX", "PX"} and index + 1 < len(upper):
                    try:
                        duration = int(args[index + 3])
                    except (ValueError, IndexError):
                        return error("value is not an integer or out of range"), False
                    if duration <= 0:
                        return error("value is not an integer or out of range"), False
                    expiry = self.store.clock() + (duration if upper[index] == "EX" else duration / 1000)
                    index += 2
                elif upper[index] in {"NX", "XX"}:
                    index += 1
                else:
                    return error("syntax error"), False
            await self.store.set(key, value, expiry)
            if self.aof is not None:
                self.aof.append({"op": "SET", "key": key, "value": value, "expire_at": expiry})
            return simple("OK"), False
        if command in {"INCR", "DECR"}:
            if len(args) != 1:
                return error(f"wrong number of arguments for '{command.lower()}' command"), False
            value, valid = await self.store.increment(args[0], 1 if command == "INCR" else -1)
            return (f":{value}\r\n".encode() if valid else error("value is not an integer or out of range")), False
        if command == "DEL":
            return (f":{await self.store.delete(*args)}\r\n".encode() if args else error("wrong number of arguments for 'del' command")), False
        if command == "EXISTS":
            return (f":{sum(await self.store.exists(key) for key in args)}\r\n".encode() if args else error("wrong number of arguments for 'exists' command")), False
        if command == "TTL":
            return (f":{await self.store.ttl(args[0])}\r\n".encode() if len(args) == 1 else error("wrong number of arguments for 'ttl' command")), False
        if command == "EXPIRE":
            if len(args) != 2:
                return error("wrong number of arguments for 'expire' command"), False
            try:
                seconds = int(args[1])
            except ValueError:
                return error("value is not an integer or out of range"), False
            return f":{int(await self.store.expire(args[0], seconds))}\r\n".encode(), False
        if command == "KEYS":
            if len(args) != 1:
                return error("wrong number of arguments for 'keys' command"), False
            keys = await self.store.keys(args[0])
            return b"*" + str(len(keys)).encode() + b"\r\n" + b"".join(bulk(key) for key in keys), False
        if command == "FLUSHALL":
            if args:
                return error("wrong number of arguments for 'flushall' command"), False
            await self.store.flushall()
            if self.aof is not None:
                self.aof.truncate()
            return simple("OK"), False
        return error(f"unknown command '{command}'"), False
