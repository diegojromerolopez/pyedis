from __future__ import annotations

import json
import os
from typing import Any

from .store import Store


class AOF:
    def __init__(self, path: str, fsync: bool = True) -> None:
        self.path = path
        self.fsync = fsync
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._file = open(path, "a", encoding="utf-8")

    def append(self, record: dict[str, Any]) -> None:
        self._file.write(json.dumps(record, separators=(",", ":")) + "\n")
        self._file.flush()
        if self.fsync:
            os.fsync(self._file.fileno())

    def close(self) -> None:
        if not self._file.closed:
            self._file.flush()
            self._file.close()

    def truncate(self) -> None:
        self._file.flush()
        self._file.close()
        with open(self.path, "w", encoding="utf-8"):
            pass
        self._file = open(self.path, "a", encoding="utf-8")

    async def replay(self, store: Store) -> None:
        if not os.path.exists(self.path):
            return
        with open(self.path, encoding="utf-8") as source:
            for line in source:
                try:
                    record = json.loads(line)
                    op = record["op"]
                    if op == "SET":
                        expiry = record.get("expire_at")
                        if expiry is None or float(expiry) > store.clock():
                            await store.set(record["key"], record["value"], expiry)
                    elif op == "DEL":
                        await store.delete(record["key"])
                    elif op in {"INCR", "DECR"}:
                        await store.increment(record["key"], 1 if op == "INCR" else -1)
                    elif op == "EXPIRE":
                        expiry = float(record["expire_at"])
                        if expiry > store.clock():
                            await store.set(record["key"], (await store.get(record["key"])) or "", expiry)
                    elif op == "FLUSHALL":
                        await store.flushall()
                except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                    print("pyedis: ignoring corrupt trailing AOF line")
                    break
