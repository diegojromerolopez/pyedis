import time
from collections.abc import Callable
from typing import Any

from src.persistence import AOFLogger
from src.resp import (
    encode_array,
    encode_bulk_string,
    encode_error,
    encode_integer,
    encode_simple_string,
)
from src.store import Store


class CommandDispatcher:
    def __init__(
        self,
        store: Store,
        aof: AOFLogger | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.store = store
        self.aof = aof
        self.clock = clock

    async def dispatch(self, args: list[bytes]) -> tuple[bytes, bool]:
        if not args:
            return b"", False
        cmd = args[0].decode("utf-8", errors="replace").upper()
        raw_args = args[1:]

        async with self.store.lock:
            if cmd == "PING":
                if len(raw_args) > 1:
                    return encode_error("ERR", "wrong number of arguments for 'ping' command"), False
                if len(raw_args) == 0:
                    return encode_simple_string("PONG"), False
                return encode_bulk_string(raw_args[0]), False

            elif cmd == "ECHO":
                if len(raw_args) != 1:
                    return encode_error("ERR", "wrong number of arguments for 'echo' command"), False
                return encode_bulk_string(raw_args[0]), False

            elif cmd == "QUIT":
                if len(raw_args) != 0:
                    return encode_error("ERR", "wrong number of arguments for 'quit' command"), False
                return encode_simple_string("OK"), True

            elif cmd == "SET":
                return self._handle_set(raw_args)

            elif cmd == "GET":
                if len(raw_args) != 1:
                    return encode_error("ERR", "wrong number of arguments for 'get' command"), False
                val = self.store.get(raw_args[0].decode("utf-8"))
                return encode_bulk_string(val), False

            elif cmd == "DEL":
                if len(raw_args) < 1:
                    return encode_error("ERR", "wrong number of arguments for 'del' command"), False
                keys = [k.decode("utf-8") for k in raw_args]
                cnt = self.store.delete(keys)
                if self.aof:
                    for k in keys:
                        self.aof.log({"op": "DEL", "key": k})
                return encode_integer(cnt), False

            elif cmd == "EXISTS":
                if len(raw_args) < 1:
                    return encode_error("ERR", "wrong number of arguments for 'exists' command"), False
                keys = [k.decode("utf-8") for k in raw_args]
                cnt = self.store.exists(keys)
                return encode_integer(cnt), False

            elif cmd == "INCR":
                if len(raw_args) != 1:
                    return encode_error("ERR", "wrong number of arguments for 'incr' command"), False
                key = raw_args[0].decode("utf-8")
                try:
                    res = self.store.incrby(key, 1)
                    if self.aof:
                        self.aof.log({"op": "INCR", "key": key})
                    return encode_integer(res), False
                except ValueError:
                    return encode_error("ERR", "value is not an integer or out of range"), False

            elif cmd == "DECR":
                if len(raw_args) != 1:
                    return encode_error("ERR", "wrong number of arguments for 'decr' command"), False
                key = raw_args[0].decode("utf-8")
                try:
                    res = self.store.incrby(key, -1)
                    if self.aof:
                        self.aof.log({"op": "DECR", "key": key})
                    return encode_integer(res), False
                except ValueError:
                    return encode_error("ERR", "value is not an integer or out of range"), False

            elif cmd == "EXPIRE":
                if len(raw_args) != 2:
                    return encode_error("ERR", "wrong number of arguments for 'expire' command"), False
                key = raw_args[0].decode("utf-8")
                try:
                    seconds = int(raw_args[1].decode("utf-8"))
                except ValueError:
                    return encode_error("ERR", "value is not an integer or out of range"), False
                if seconds <= 0:
                    cnt = self.store.delete([key])
                    return encode_integer(cnt), False
                exp_at = self.clock() + seconds
                ok = self.store.expire(key, exp_at)
                if ok and self.aof:
                    self.aof.log({"op": "EXPIRE", "key": key, "expire_at": exp_at})
                return encode_integer(1 if ok else 0), False

            elif cmd == "TTL":
                if len(raw_args) != 1:
                    return encode_error("ERR", "wrong number of arguments for 'ttl' command"), False
                key = raw_args[0].decode("utf-8")
                return encode_integer(self.store.ttl(key)), False

            elif cmd == "KEYS":
                if len(raw_args) != 1:
                    return encode_error("ERR", "wrong number of arguments for 'keys' command"), False
                pat = raw_args[0].decode("utf-8")
                found = self.store.keys(pat)
                return encode_array([k.encode("utf-8") for k in found]), False

            elif cmd == "FLUSHALL":
                self.store.flushall()
                if self.aof:
                    self.aof.truncate()
                return encode_simple_string("OK"), False

            elif cmd in ("COMMAND", "INFO", "CLIENT"):
                return encode_array([]), False

            else:
                return encode_error("ERR", f"unknown command '{cmd}'"), False

    def _handle_set(self, raw_args: list[bytes]) -> tuple[bytes, bool]:
        if len(raw_args) < 2:
            return encode_error("ERR", "wrong number of arguments for 'set' command"), False
        key = raw_args[0].decode("utf-8")
        val = raw_args[1]
        i = 2
        nx = False
        xx = False
        expire_at: float | None = None
        while i < len(raw_args):
            opt = raw_args[i].decode("utf-8").upper()
            if opt == "NX":
                nx = True
            elif opt == "XX":
                xx = True
            elif opt in ("EX", "PX"):
                if i + 1 >= len(raw_args):
                    return encode_error("ERR", "syntax error"), False
                try:
                    dur = float(raw_args[i + 1].decode("utf-8"))
                    if dur <= 0:
                        return encode_error("ERR", "value is not an integer or out of range"), False
                except ValueError:
                    return encode_error("ERR", "value is not an integer or out of range"), False
                if opt == "PX":
                    dur = dur / 1000.0
                expire_at = self.clock() + dur
                i += 1
            else:
                return encode_error("ERR", "syntax error"), False
            i += 1

        if nx and xx:
            return encode_error("ERR", "syntax error"), False

        exists = self.store.exists([key]) > 0
        if nx and exists:
            return encode_bulk_string(None), False
        if xx and not exists:
            return encode_bulk_string(None), False

        self.store.set(key, val, expire_at)
        if self.aof:
            self.aof.log(
                {
                    "op": "SET",
                    "key": key,
                    "value": val.decode("utf-8", errors="latin1"),
                    "expire_at": expire_at,
                }
            )
        return encode_simple_string("OK"), False
