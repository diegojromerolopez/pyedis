"""Append-only persistence."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .store import Store


class AOF:
    def __init__(self, directory: str, fsync: bool = True) -> None:
        self.path = Path(directory) / "dump.aof"
        self.fsync_enabled = fsync
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def append(self, record: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
            handle.flush()
            if self.fsync_enabled:
                os.fsync(handle.fileno())

    def flush(self) -> None:
        self.path.write_text("", encoding="utf-8")
        if self.fsync_enabled:
            with self.path.open("a") as handle:
                os.fsync(handle.fileno())

    def replay(self, store: Store) -> None:
        lines = self.path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            try:
                record = json.loads(line)
                op = record["op"]
                if op == "SET":
                    store.set(record["key"], record["value"], record.get("expire_at"))
                elif op == "DEL":
                    store.delete([record["key"]])
                elif op in ("INCR", "DECR"):
                    item = store.get(record["key"])
                    value = int(item.value) if item else 0
                    value += 1 if op == "INCR" else -1
                    store.set(record["key"], str(value), item.expire_at if item else None)
                elif op == "EXPIRE":
                    item = store.get(record["key"])
                    if item:
                        item.expire_at = record["expire_at"]
                elif op == "FLUSHALL":
                    store.flush()
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                if index == len(lines) - 1:
                    print("pyedis: ignoring corrupt trailing AOF line")
                    return
                raise RuntimeError(f"corrupt AOF line: {exc}") from exc
