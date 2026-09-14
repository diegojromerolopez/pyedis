import time
from typing import Callable, Any
from src.store import Store
from src.persistence import AOFLogger
from src.resp import encode_resp, encode_error, encode_simple_string


class CommandDispatcher:
    def __init__(
        self,
        store: Store,
        aof: AOFLogger,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.store = store
        self.aof = aof
        self.clock = clock

    async def dispatch(self, args: list[bytes]) -> tuple[bytes, bool]:
        if not args:
            return b"", False
        cmd = args[0].decode("utf-8").upper()
        raw_args = [a.decode("utf-8", errors="replace") for a in args[1:]]

        async with self.store.lock:
            return self._execute(cmd, raw_args)

    def _execute(self, cmd: str, args: list[str]) -> tuple[bytes, bool]:
        if cmd == "PING":
            if len(args) == 0:
                return encode_simple_string("PONG"), False
            if len(args) == 1:
                return encode_resp(args[0]), False
            return (
                encode_error("wrong number of arguments for 'ping' command"),
                False,
            )
        if cmd == "ECHO":
            if len(args) != 1:
                return (
                    encode_error("wrong number of arguments for 'echo' command"),
                    False,
                )
            return encode_resp(args[0]), False
        if cmd == "QUIT":
            if len(args) != 0:
                return (
                    encode_error("wrong number of arguments for 'quit' command"),
                    False,
                )
            return encode_simple_string("OK"), True
        if cmd == "COMMAND":
            return encode_resp([]), False
        if cmd == "INFO" or cmd == "CLIENT":
            return encode_simple_string("OK"), False
        if cmd == "SET":
            return self._cmd_set(args)
        if cmd == "GET":
            if len(args) != 1:
                return (
                    encode_error("wrong number of arguments for 'get' command"),
                    False,
                )
            return encode_resp(self.store.get(args[0])), False
        if cmd == "DEL":
            if len(args) < 1:
                return (
                    encode_error("wrong number of arguments for 'del' command"),
                    False,
                )
            cnt = self.store.delete(args)
            for k in args:
                self.aof.append({"op": "DEL", "key": k})
            return encode_resp(cnt), False
        if cmd == "EXISTS":
            if len(args) < 1:
                return (
                    encode_error(
                        "wrong number of arguments for 'exists' command"
                    ),
                    False,
                )
            return encode_resp(self.store.exists(args)), False
        if cmd == "INCR":
            if len(args) != 1:
                return (
                    encode_error("wrong number of arguments for 'incr' command"),
                    False,
                )
            try:
                val = self.store.incr(args[0], 1)
                self.aof.append({"op": "INCR", "key": args[0]})
                return encode_resp(val), False
            except ValueError as e:
                return encode_error(str(e)), False
        if cmd == "DECR":
            if len(args) != 1:
                return (
                    encode_error("wrong number of arguments for 'decr' command"),
                    False,
                )
            try:
                val = self.store.incr(args[0], -1)
                self.aof.append({"op": "DECR", "key": args[0]})
                return encode_resp(val), False
            except ValueError as e:
                return encode_error(str(e)), False
        if cmd == "EXPIRE":
            if len(args) != 2:
                return (
                    encode_error(
                        "wrong number of arguments for 'expire' command"
                    ),
                    False,
                )
            try:
                sec = float(args[1])
            except ValueError:
                return (
                    encode_error("value is not an integer or out of range"),
                    False,
                )
            res = self.store.expire(args[0], sec)
            if res == 1:
                expire_at = self.clock() + sec
                self.aof.append(
                    {"op": "EXPIRE", "key": args[0], "expire_at": expire_at}
                )
            return encode_resp(res), False
        if cmd == "TTL":
            if len(args) != 1:
                return (
                    encode_error("wrong number of arguments for 'ttl' command"),
                    False,
                )
            return encode_resp(self.store.ttl(args[0])), False
        if cmd == "KEYS":
            if len(args) != 1:
                return (
                    encode_error("wrong number of arguments for 'keys' command"),
                    False,
                )
            return encode_resp(self.store.keys(args[0])), False
        if cmd == "FLUSHALL":
            self.store.flushall()
            self.aof.truncate()
            return encode_simple_string("OK"), False

        return encode_error(f"unknown command '{cmd}'"), False

    def _cmd_set(self, args: list[str]) -> tuple[bytes, bool]:
        if len(args) < 2:
            return (
                encode_error("wrong number of arguments for 'set' command"),
                False,
            )
        key = args[0]
        val = args[1]
        idx = 2
        expire_at: float | None = None
        nx = False
        xx = False

        while idx < len(args):
            flag = args[idx].upper()
            if flag == "EX" and idx + 1 < len(args):
                try:
                    sec = float(args[idx + 1])
                    if sec <= 0:
                        raise ValueError()
                    expire_at = self.clock() + sec
                except ValueError:
                    return (
                        encode_error("value is not an integer or out of range"),
                        False,
                    )
                idx += 2
            elif flag == "PX" and idx + 1 < len(args):
                try:
                    ms = float(args[idx + 1])
                    if ms <= 0:
                        raise ValueError()
                    expire_at = self.clock() + (ms / 1000.0)
                except ValueError:
                    return (
                        encode_error("value is not an integer or out of range"),
                        False,
                    )
                idx += 2
            elif flag == "NX":
                nx = True
                idx += 1
            elif flag == "XX":
                xx = True
                idx += 1
            else:
                return encode_error("syntax error"), False

        if nx and xx:
            return encode_error("syntax error"), False

        exists = self.store.exists([key]) > 0
        if nx and exists:
            return encode_resp(None), False
        if xx and not exists:
            return encode_resp(None), False

        self.store.set(key, val, expire_at)
        record: dict[str, Any] = {"op": "SET", "key": key, "value": val}
        if expire_at is not None:
            record["expire_at"] = expire_at
        self.aof.append(record)
        return encode_simple_string("OK"), False
