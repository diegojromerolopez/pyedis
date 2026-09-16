"""Append-only persistence with absolute expiration timestamps."""

from __future__ import annotations

import json
import logging
import os
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
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
                op = record["op"]
                if op == "SET":
                    expiry = record.get("expire_at")
                    if expiry is None or float(expiry) > store.clock():
                        await store.set(record["key"], record["value"], expiry)
                elif op == "DEL":
                    await store.delete([record["key"]])
                elif op in ("INCR", "DECR"):
                    await store.incr(record["key"], 1 if op == "INCR" else -1)
                elif op == "EXPIRE":
                    if float(record["expire_at"]) <= store.clock():
                        await store.delete([record["key"]])
                    else:
                        async with store.lock:
                            if record["key"] in store.values:
                                store.expirations[record["key"]] = float(record["expire_at"])
                elif op == "FLUSHALL":
                    await store.flush()
            except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                logging.warning("pyedis: ignoring corrupt trailing AOF line")
