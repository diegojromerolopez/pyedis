from __future__ import annotations

from src.resp import (
    encode_bulk_string,
    encode_error,
    encode_integer,
    encode_simple_string,
)
from src.store import Store


class CommandDispatcher:
    def __init__(self, store: Store) -> None:
        self.store = store

    async def dispatch(self, args: list[bytes]) -> bytes:
        if not args:
            return encode_error("ERR empty command")

        cmd_str = args[0].decode("utf-8", errors="replace").lower()

        if cmd_str == "get":
            if len(args) != 2:
                return encode_error("ERR wrong number of arguments for 'get' command")
            key = args[1].decode("utf-8")
            val = await self.store.get(key)
            return encode_bulk_string(val)

        elif cmd_str == "set":
            if len(args) != 3:
                return encode_error("ERR wrong number of arguments for 'set' command")
            key = args[1].decode("utf-8")
            val = args[2].decode("utf-8")
            await self.store.set(key, val)
            return encode_simple_string("OK")

        elif cmd_str == "del":
            if len(args) < 2:
                return encode_error("ERR wrong number of arguments for 'del' command")
            keys = [a.decode("utf-8") for a in args[1:]]
            count = await self.store.delete(*keys)
            return encode_integer(count)

        elif cmd_str == "exists":
            if len(args) < 2:
                return encode_error(
                    "ERR wrong number of arguments for 'exists' command"
                )
            keys = [a.decode("utf-8") for a in args[1:]]
            count = await self.store.exists(*keys)
            return encode_integer(count)

        else:
            return encode_error(f"ERR unknown command '{cmd_str}'")
