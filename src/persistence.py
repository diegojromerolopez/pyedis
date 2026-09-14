from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from .store import Store


class AOF:
    def __init__(self, path: str | Path, fsync: bool = True) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fsync = fsync

    def append(self, record: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
            handle.flush()
            if self.fsync:
                os.fsync(handle.fileno())

    def truncate(self) -> None:
        self.path.write_text("", encoding="utf-8")

    async def replay(self, store: Store) -> None:
        if not self.path.exists():
            return
        lines = self.path.read_text(encoding="utf-8", errors="replace").splitlines()
        for number, line in enumerate(lines):
            try:
                record = json.loads(line)
                op = record["op"]
                if op == "SET":
                    expiry = record.get("expire_at")
                    await store.set(record["key"], record["value"].encode(), expiry)
                elif op == "DEL":
                    await store.delete([record["key"]])
                elif op == "INCR":
                    await store.increment(record["key"], 1)
                elif op == "DECR":
                    await store.increment(record["key"], -1)
                elif op == "EXPIRE":
                    async with store.lock:
                        store._purge(record["key"])
                        if record["key"] in store.values:
                            store.expirations[record["key"]] = float(record["expire_at"])
                elif op == "FLUSHALL":
                    await store.flush()
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                if number == len(lines) - 1:
                    print("pyedis: ignoring corrupt trailing AOF line", file=sys.stderr)
                else:
                    print(f"pyedis: ignoring corrupt AOF line {number + 1}", file=sys.stderr)
