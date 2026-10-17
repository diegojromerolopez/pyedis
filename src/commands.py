"""Command dispatcher and Redis parity handlers."""

from src.persistence import AOFLogger
from src.resp import (
    encode_array,
    encode_bulk_string,
    encode_error,
    encode_integer,
    encode_simple_string,
)
from src.store import Store
from src.handlers.geospatial.geoadd import execute_geoadd


class CommandDispatcher:
    def __init__(self, store: Store, aof: AOFLogger | None = None) -> None:
        self.store: Store = store
        self.aof: AOFLogger | None = aof

    async def dispatch(self, args: list[bytes]) -> tuple[bytes, bool]:
        if not args:
            return encode_error("empty command"), False
        cmd = args[0].decode("utf-8").upper()
        cmd_args = [a.decode("utf-8", errors="replace") for a in args[1:]]

        async with self.store.lock:
            if cmd == "PING":
                if not cmd_args:
                    return encode_simple_string("PONG"), False
                return encode_bulk_string(cmd_args[0]), False

            elif cmd == "ECHO":
                if len(cmd_args) != 1:
                    return encode_error("wrong number of arguments for 'echo' command"), False
                return encode_bulk_string(cmd_args[0]), False

            elif cmd == "QUIT":
                return encode_simple_string("OK"), True

            elif cmd == "SET":
                if len(cmd_args) < 2:
                    return encode_error("wrong number of arguments for 'set' command"), False
                key, val = cmd_args[0], cmd_args[1]
                ex_sec = None
                nx = False
                xx = False
                idx = 2
                while idx < len(cmd_args):
                    opt = cmd_args[idx].upper()
                    if opt in ("EX", "PX"):
                        if idx + 1 >= len(cmd_args):
                            return encode_error("syntax error"), False
                        try:
                            duration = float(cmd_args[idx + 1])
                        except ValueError:
                            return encode_error("invalid expire time in 'set' command"), False
                        if duration <= 0:
                            return encode_error("invalid expire time in 'set' command"), False
                        ex_sec = duration if opt == "EX" else duration / 1000.0
                        idx += 2
                    elif opt == "NX":
                        if nx:
                            return encode_error("syntax error"), False
                        nx = True
                        idx += 1
                    elif opt == "XX":
                        if xx:
                            return encode_error("syntax error"), False
                        xx = True
                        idx += 1
                    else:
                        return encode_error("syntax error"), False

                expire_at = (self.store._clock() + ex_sec) if ex_sec else None
                ok = self.store.set(key, val, expire_at=expire_at, nx=nx, xx=xx)
                if ok:
                    if self.aof:
                        self.aof.log_mutation(
                            {"op": "SET", "key": key, "value": val, "expire_at": expire_at}
                        )
                    return encode_simple_string("OK"), False
                return encode_bulk_string(None), False

            elif cmd == "GET":
                if len(cmd_args) != 1:
                    return encode_error("wrong number of arguments for 'get' command"), False
                val = self.store.get(cmd_args[0])
                return encode_bulk_string(val), False

            elif cmd == "DEL":
                if not cmd_args:
                    return encode_error("wrong number of arguments for 'del' command"), False
                count = self.store.delete(*cmd_args)
                if count > 0 and self.aof:
                    for k in cmd_args:
                        self.aof.log_mutation({"op": "DEL", "key": k})
                return encode_integer(count), False

            elif cmd == "EXISTS":
                if not cmd_args:
                    return encode_error("wrong number of arguments for 'exists' command"), False
                return encode_integer(self.store.exists(*cmd_args)), False

            elif cmd == "INCR":
                if len(cmd_args) != 1:
                    return encode_error("wrong number of arguments for 'incr' command"), False
                try:
                    res = self.store.incr_by(cmd_args[0], 1)
                    if self.aof:
                        self.aof.log_mutation({"op": "INCR", "key": cmd_args[0]})
                    return encode_integer(res), False
                except ValueError as e:
                    return encode_error(str(e)), False

            elif cmd == "DECR":
                if len(cmd_args) != 1:
                    return encode_error("wrong number of arguments for 'decr' command"), False
                try:
                    res = self.store.incr_by(cmd_args[0], -1)
                    if self.aof:
                        self.aof.log_mutation({"op": "DECR", "key": cmd_args[0]})
                    return encode_integer(res), False
                except ValueError as e:
                    return encode_error(str(e)), False

            elif cmd == "EXPIRE":
                if len(cmd_args) != 2:
                    return encode_error("wrong number of arguments for 'expire' command"), False
                try:
                    seconds = float(cmd_args[1])
                except ValueError:
                    return encode_error("value is not an integer or out of range"), False
                ok = self.store.expire(cmd_args[0], seconds)
                if ok and self.aof:
                    self.aof.log_mutation(
                        {
                            "op": "EXPIRE",
                            "key": cmd_args[0],
                            "expire_at": self.store._expires.get(cmd_args[0]),
                        }
                    )
                return encode_integer(1 if ok else 0), False

            elif cmd == "TTL":
                if len(cmd_args) != 1:
                    return encode_error("wrong number of arguments for 'ttl' command"), False
                return encode_integer(self.store.ttl(cmd_args[0])), False

            elif cmd == "KEYS":
                if len(cmd_args) != 1:
                    return encode_error("wrong number of arguments for 'keys' command"), False
                return encode_array(self.store.keys(cmd_args[0])), False

            elif cmd == "FLUSHALL":
                self.store.flushall()
                if self.aof:
                    self.aof.truncate()
                return encode_simple_string("OK"), False

            elif cmd == "GEOADD":
                result = execute_geoadd(self.store, cmd_args)
                if result.changed and self.aof:
                    self.aof.log_mutation({"op": "GEOADD", "args": cmd_args})
                return result.reply, False

            elif cmd in ("COMMAND", "CLIENT", "INFO", "HELLO"):
                return encode_simple_string("OK"), False

            return encode_error(f"unknown command '{cmd}'"), False
