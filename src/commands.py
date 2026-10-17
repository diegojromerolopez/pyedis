"""Command validation, execution routing, and RESP envelope generation."""

import time
from src.persistence import AOFLogger
from src.resp import encode_bulk_string, encode_error, encode_integer, encode_simple_string
from src.store import Store


class CommandDispatcher:
    def __init__(self, store: Store, aof: AOFLogger | None = None) -> None:
        self.store: Store = store
        self.aof: AOFLogger | None = aof

    async def dispatch(self, args: list[bytes]) -> tuple[bytes, bool]:
        if not args:
            return encode_error("empty command"), False

        cmd = args[0].decode("utf-8", errors="ignore").upper()
        str_args = [a.decode("utf-8", errors="ignore") for a in args[1:]]

        async with self.store.lock:
            if cmd == "PING":
                if not str_args:
                    return encode_simple_string("PONG"), False
                return encode_bulk_string(str_args[0]), False
            elif cmd == "ECHO":
                if len(str_args) != 1:
                    return encode_error("wrong number of arguments for 'echo' command"), False
                return encode_bulk_string(str_args[0]), False
            elif cmd == "QUIT":
                return encode_simple_string("OK"), True
            elif cmd == "SET":
                if len(str_args) < 2:
                    return encode_error("wrong number of arguments for 'set' command"), False
                key, val = str_args[0], str_args[1]
                expire_at = None
                nx = False
                xx = False
                idx = 2
                while idx < len(str_args):
                    opt = str_args[idx].upper()
                    if opt == "EX" and idx + 1 < len(str_args):
                        expire_at = time.time() + float(str_args[idx + 1])
                        idx += 2
                    elif opt == "PX" and idx + 1 < len(str_args):
                        expire_at = time.time() + (float(str_args[idx + 1]) / 1000.0)
                        idx += 2
                    elif opt == "NX":
                        nx = True
                        idx += 1
                    elif opt == "XX":
                        xx = True
                        idx += 1
                    else:
                        return encode_error("syntax error"), False
                res = self.store.set(key, val, expire_at=expire_at, nx=nx, xx=xx)
                if res:
                    if self.aof:
                        self.aof.log_mutation(
                            {"op": "SET", "key": key, "value": val, "expire_at": expire_at}
                        )
                    return encode_simple_string("OK"), False
                return encode_bulk_string(None), False
            elif cmd == "GET":
                if len(str_args) != 1:
                    return encode_error("wrong number of arguments for 'get' command"), False
                val = self.store.get(str_args[0])
                return encode_bulk_string(val), False
            elif cmd == "DEL":
                if not str_args:
                    return encode_error("wrong number of arguments for 'del' command"), False
                count = self.store.delete(*str_args)
                if self.aof and count > 0:
                    for k in str_args:
                        self.aof.log_mutation({"op": "DEL", "key": k})
                return encode_integer(count), False
            elif cmd == "EXISTS":
                if not str_args:
                    return encode_error("wrong number of arguments for 'exists' command"), False
                return encode_integer(self.store.exists(*str_args)), False
            elif cmd == "INCR":
                if len(str_args) != 1:
                    return encode_error("wrong number of arguments for 'incr' command"), False
                try:
                    res_val = self.store.incr_by(str_args[0], 1)
                    if self.aof:
                        self.aof.log_mutation(
                            {
                                "op": "SET",
                                "key": str_args[0],
                                "value": str(res_val),
                                "expire_at": self.store._expires.get(str_args[0]),
                            }
                        )
                    return encode_integer(res_val), False
                except ValueError as e:
                    return encode_error(str(e)), False
            elif cmd == "DECR":
                if len(str_args) != 1:
                    return encode_error("wrong number of arguments for 'decr' command"), False
                try:
                    res_val = self.store.incr_by(str_args[0], -1)
                    if self.aof:
                        self.aof.log_mutation(
                            {
                                "op": "SET",
                                "key": str_args[0],
                                "value": str(res_val),
                                "expire_at": self.store._expires.get(str_args[0]),
                            }
                        )
                    return encode_integer(res_val), False
                except ValueError as e:
                    return encode_error(str(e)), False
            elif cmd == "TTL":
                if len(str_args) != 1:
                    return encode_error("wrong number of arguments for 'ttl' command"), False
                return encode_integer(self.store.ttl(str_args[0])), False
            elif cmd == "EXPIRE":
                if len(str_args) != 2:
                    return encode_error("wrong number of arguments for 'expire' command"), False
                try:
                    sec = float(str_args[1])
                    res_bool = self.store.expire(str_args[0], sec)
                    if res_bool and self.aof:
                        self.aof.log_mutation(
                            {
                                "op": "EXPIRE",
                                "key": str_args[0],
                                "expire_at": self.store._expires.get(str_args[0]),
                            }
                        )
                    return encode_integer(1 if res_bool else 0), False
                except ValueError:
                    return encode_error("value is not an integer or out of range"), False
            elif cmd == "KEYS":
                if len(str_args) != 1:
                    return encode_error("wrong number of arguments for 'keys' command"), False
                matched_keys = self.store.keys(str_args[0])
                return encode_bulk_string("\r\n".join(matched_keys)) if False else encode_array(
                    [encode_bulk_string(k) for k in matched_keys]
                ), False
            elif cmd == "FLUSHALL":
                self.store.flushall()
                if self.aof:
                    self.aof.truncate()
                return encode_simple_string("OK"), False
            elif cmd in ("COMMAND", "CLIENT", "INFO", "HELLO"):
                return encode_simple_string("OK"), False
            else:
                return encode_error(f"unknown command '{cmd}'"), False
