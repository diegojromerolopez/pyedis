from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


class AOF:
    def __init__(self, directory: str, fsync: bool = True) -> None:
        self.path = Path(directory) / "dump.aof"
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

    async def replay(self, store: Any) -> None:
        if not self.path.exists():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
                op = record["op"]
                if op == "SET":
                    await store.set(
                        record["key"], record["value"].encode(), record.get("expire_at")
                    )
                elif op == "DEL":
                    await store.delete([record["key"]])
                elif op == "EXPIRE":
                    await store.set(
                        record["key"],
                        await store.get(record["key"]),
                        record["expire_at"],
                    )
                elif op == "FLUSHALL":
                    await store.flush()
                elif op in ("INCR", "DECR"):
                    await store.number(record["key"], 1 if op == "INCR" else -1)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                print("pyedis: ignoring corrupt trailing AOF line", file=sys.stderr)
