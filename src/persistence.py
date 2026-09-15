"""Append-only file persistence."""
from __future__ import annotations

import json
import os
from pathlib import Path
from collections.abc import Callable
from .store import Store


class Persistence:
    def __init__(self, directory: str, fsync: bool = True, clock: Callable[[], float] | None = None) -> None:
        self.directory = Path(directory)
        self.path = self.directory / "dump.aof"
        self.fsync_enabled = fsync
        self.clock = clock

    def open(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def append(self, record: dict[str, object]) -> None:
        with self.path.open("ab") as handle:
            handle.write(json.dumps(record, separators=(",", ":")).encode() + b"\n")
            handle.flush()
            if self.fsync_enabled:
                os.fsync(handle.fileno())

    def flush(self) -> None:
        self.path.write_bytes(b"")
        if self.fsync_enabled:
            with self.path.open("ab") as handle:
                os.fsync(handle.fileno())

    def replay(self, store: Store, warn: Callable[[str], None]) -> None:
        if not self.path.exists():
            return
        lines = self.path.read_bytes().splitlines()
        for index, raw in enumerate(lines):
            try:
                record = json.loads(raw)
                op = record["op"]
                key = str(record.get("key", "")).encode()
                if op == "SET":
                    expiry = record.get("expire_at")
                    if expiry is None or expiry > store.clock():
                        store.set(key, str(record["value"]).encode(), expiry)
                elif op == "DEL":
                    store.delete(key)
                elif op in ("INCR", "DECR"):
                    old = store.get(key) or b"0"
                    number = int(old) + (1 if op == "INCR" else -1)
                    expiry = store.data[key].expire_at if key in store.data else None
                    store.set(key, str(number).encode(), expiry)
                elif op == "EXPIRE":
                    if store.exists(key):
                        store.data[key].expire_at = float(record["expire_at"])
                elif op == "FLUSHALL":
                    store.data.clear()
            except Exception as exc:
                if index == len(lines) - 1:
                    warn("pyedis: ignoring corrupt trailing AOF line")
                    return
                raise RuntimeError(f"invalid AOF record: {exc}") from exc
