"""Append-Only File (AOF) durability engine."""

import json
import os
from pathlib import Path
from typing import Any
from src.store import Store
from src.handlers.geospatial.geoadd import execute_geoadd


class AOFLogger:
    def __init__(self, filepath: str | Path, fsync: bool = True) -> None:
        self.filepath: Path = Path(filepath)
        self.fsync: bool = fsync
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.filepath, "a", encoding="utf-8")

    def log_mutation(self, record: dict[str, Any]) -> None:
        line = json.dumps(record) + "\n"
        self._file.write(line)
        self._file.flush()
        if self.fsync:
            os.fsync(self._file.fileno())

    def truncate(self) -> None:
        self._file.close()
        self._file = open(self.filepath, "w", encoding="utf-8")
        self._file.flush()
        if self.fsync:
            os.fsync(self._file.fileno())

    def close(self) -> None:
        self._file.close()


def replay_aof(filepath: str | Path, store: Store) -> int:
    p = Path(filepath)
    if not p.exists():
        return 0
    replayed = 0
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                print("pyedis: ignoring corrupt trailing AOF line")
                break
            op = rec.get("op")
            if op == "SET":
                store.set(rec["key"], rec["value"], expire_at=rec.get("expire_at"))
            elif op == "DEL":
                store.delete(rec["key"])
            elif op == "INCR":
                store.incr_by(rec["key"], 1)
            elif op == "DECR":
                store.incr_by(rec["key"], -1)
            elif op == "EXPIRE":
                if rec.get("expire_at") is not None:
                    store._expires[rec["key"]] = rec["expire_at"]
            elif op == "FLUSHALL":
                store.flushall()
            elif op == "GEOADD":
                from src.handlers.geospatial.geoadd import execute_geoadd

                execute_geoadd(store, rec["args"])
            replayed += 1
    return replayed
