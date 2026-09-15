"""Command execution."""
from __future__ import annotations

import re
from typing import Any

from .persistence import AOF
from .resp import encode, error, simple
from .store import Store

_INT = re.compile(r"^-?[0-9]+$")


class Commands:
    def __init__(self, store: Store, aof: AOF) -> None:
        self.store, self.aof = store, aof

    def run(self, raw: list[object]) -> tuple[bytes, bool]:
        if not raw or not isinstance(raw[0], (bytes, str)):
            return error("ERR protocol error"), True
        name = raw[0].decode(errors="replace") if isinstance(raw[0], bytes) else raw[0]
        name = name.upper()
        args = [x if isinstance(x, str) else x.decode(errors="surrogateescape") for x in raw[1:] if isinstance(x, (bytes, str))]
        arities = {"PING": (0, 1), "ECHO": (1, 1), "QUIT": (0, 0), "GET": (1, 1), "DEL": (1, 9999), "EXISTS": (1, 9999), "INCR": (1, 1), "DECR": (1, 1), "EXPIRE": (2, 2), "TTL": (1, 1), "KEYS": (1, 1), "FLUSHALL": (0, 0), "SET": (2, 9999)}
        if name not in arities:
            return error(f"ERR unknown command '{name}'"), False
        low, high = arities[name]
        if not low <= len(args) <= high:
            return error(f"ERR wrong number of arguments for '{name.lower()}' command"), False
        if name == "PING": return (simple("PONG") if not args else encode(args[0])), False
        if name == "ECHO": return encode(args[0]), False
        if name == "QUIT": return simple("OK"), True
        if name == "GET":
            item = self.store.get(args[0]); return encode(item.value if item else None), False
        if name == "DEL":
            count = self.store.delete(args); 
            if count: self.aof.append({"op":"DEL","key":args[0]})
            return encode(count), False
        if name == "EXISTS": return encode(sum(self.store.exists(key) for key in args)), False
        if name in ("INCR", "DECR"):
            item = self.store.get(args[0]); old = item.value if item else "0"
            try: value = int(old) + (1 if name == "INCR" else -1)
            except ValueError: return error("ERR value is not an integer or out of range"), False
            self.store.set(args[0], str(value), item.expire_at if item else None); self.aof.append({"op":name,"key":args[0]})
            return encode(value), False
        if name == "EXPIRE":
            if not _INT.match(args[1]): return error("ERR value is not an integer or out of range"), False
            seconds = int(args[1]); changed = self.store.expire(args[0], seconds)
            if changed and seconds > 0: self.aof.append({"op":"EXPIRE","key":args[0],"expire_at":self.store.get(args[0]).expire_at})
            elif changed: self.aof.append({"op":"DEL","key":args[0]})
            return encode(1 if changed else 0), False
        if name == "TTL": return encode(self.store.ttl(args[0])), False
        if name == "KEYS": return encode(self.store.keys(args[0])), False
        if name == "FLUSHALL": self.store.flush(); self.aof.flush(); return simple("OK"), False
        key, value = args[0], args[1]; expire: float | None = None; condition: str | None = None; i = 2
        while i < len(args):
            option = args[i].upper()
            if option in ("EX", "PX") and i + 1 < len(args) and _INT.match(args[i + 1]):
                number = int(args[i + 1]);
                if number <= 0: return error("ERR value is not an integer or out of range"), False
                expire = self.store.clock() + (number if option == "EX" else number / 1000); i += 2; continue
            if option in ("NX", "XX") and condition is None: condition = option; i += 1; continue
            return error("ERR syntax error"), False
        if not self.store.set(key, value, expire, condition): return encode(None), False
        self.aof.append({"op":"SET","key":key,"value":value,"expire_at":expire}); return simple("OK"), False
