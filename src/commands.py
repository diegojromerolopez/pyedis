"""Command execution."""
from __future__ import annotations

import time
from .persistence import Persistence
from .resp import RespError
from .store import Store


class Commands:
    def __init__(self, store: Store, persistence: Persistence) -> None:
        self.store, self.persistence = store, persistence

    def execute(self, args: list[bytes]) -> tuple[object, bool]:
        if not args:
            return RespError("ERR empty command"), False
        name = args[0].decode("ascii", "replace").upper()
        rest = args[1:]
        if name == "PING":
            return (b"PONG" if not rest else rest[0], False) if len(rest) <= 1 else (self._arity("ping"), False)
        if name == "ECHO":
            return (rest[0], False) if len(rest) == 1 else (self._arity("echo"), False)
        if name == "QUIT":
            return ("OK", True) if not rest else (self._arity("quit"), False)
        if name == "GET":
            return (self.store.get(rest[0]) if len(rest) == 1 else self._arity("get"), False)
        if name in ("DEL", "EXISTS"):
            if not rest:
                return self._arity(name.lower()), False
            count = sum(self.store.delete(k) for k in rest) if name == "DEL" else sum(self.store.exists(k) for k in rest)
            if name == "DEL" and count:
                self.persistence.append({"op": "DEL", "key": rest[0].decode()})
            return count, False
        if name == "SET":
            return self._set(rest)
        if name in ("INCR", "DECR"):
            return self._incr(name, rest)
        if name == "EXPIRE":
            return self._expire(rest)
        if name == "TTL":
            return (self.store.ttl(rest[0]) if len(rest) == 1 else self._arity("ttl"), False)
        if name == "KEYS":
            return (self.store.keys(rest[0]) if len(rest) == 1 else self._arity("keys"), False)
        if name == "FLUSHALL":
            if rest:
                return self._arity("flushall"), False
            self.store.data.clear(); self.persistence.append({"op": "FLUSHALL"}); self.persistence.flush()
            return "OK", False
        return RespError(f"ERR unknown command '{name}'"), False

    def _arity(self, name: str) -> RespError:
        return RespError(f"ERR wrong number of arguments for '{name}' command")

    def _set(self, args: list[bytes]) -> tuple[object, bool]:
        if len(args) < 2:
            return RespError("ERR syntax error"), False
        expiry: float | None = None; nx = xx = False; i = 2
        try:
            while i < len(args):
                option = args[i].upper()
                if option in (b"EX", b"PX") and i + 1 < len(args):
                    seconds = int(args[i + 1]); expiry = time.time() + seconds * (1 if option == b"EX" else .001); i += 2
                    if seconds <= 0: raise ValueError
                elif option == b"NX" and not nx and not xx: nx = True; i += 1
                elif option == b"XX" and not nx and not xx: xx = True; i += 1
                else: return RespError("ERR syntax error"), False
        except ValueError:
            return RespError("ERR value is not an integer or out of range"), False
        present = self.store.exists(args[0])
        if (nx and present) or (xx and not present): return None, False
        self.store.set(args[0], args[1], expiry)
        self.persistence.append({"op":"SET","key":args[0].decode(),"value":args[1].decode(),"expire_at":expiry})
        return "OK", False

    def _incr(self, name: str, args: list[bytes]) -> tuple[object, bool]:
        if len(args) != 1: return self._arity(name.lower()), False
        old = self.store.get(args[0]) or b"0"
        try: value = int(old) + (1 if name == "INCR" else -1)
        except ValueError: return RespError("ERR value is not an integer or out of range"), False
        expiry = self.store.data.get(args[0]).expire_at if args[0] in self.store.data else None
        self.store.set(args[0], str(value).encode(), expiry); self.persistence.append({"op":name,"key":args[0].decode()})
        return value, False

    def _expire(self, args: list[bytes]) -> tuple[object, bool]:
        if len(args) != 2: return self._arity("expire"), False
        try: seconds = int(args[1])
        except ValueError: return RespError("ERR value is not an integer or out of range"), False
        if not self.store.exists(args[0]): return 0, False
        if seconds <= 0: self.store.delete(args[0])
        else: self.store.data[args[0]].expire_at = time.time() + seconds
        self.persistence.append({"op":"EXPIRE","key":args[0].decode(),"expire_at":time.time() + seconds}); return 1, False
