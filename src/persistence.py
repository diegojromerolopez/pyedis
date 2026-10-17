"""Append-Only File (AOF) durability engine with absolute timestamps."""
import json
import os
from pathlib import Path
from typing import Any
from src.store import Store

class AOFLogger:
    def __init__(self, filepath: str | Path, fsync: bool = True) -> None:
        self.filepath: Path = Path(filepath)
        self.fsync: bool = fsync

    def log_mutation(self, record: dict[str, Any]) -> None:
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record) + "\n"
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            if self.fsync:
                os.fsync(f.fileno())

    def truncate(self) -> None:
        if self.filepath.exists():
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.truncate(0)

def replay_aof(filepath: str | Path, store: Store) -> int:
    path = Path(filepath)
    if not path.exists():
        return 0
    replayed = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                print("pyedis: ignoring corrupt trailing AOF line")
                continue
            op = rec.get("op")
            if op == "SET":
                store.set(rec["key"], rec["value"], expire_at=rec.get("expire_at"))
                replayed += 1
            elif op == "DEL":
                store.delete(rec["key"])
                replayed += 1
            elif op == "EXPIRE":
                store._expires[rec["key"]] = rec["expire_at"]
                replayed += 1
            elif op == "FLUSHALL":
                store.flushall()
                replayed += 1
    return replayed
