"""Append-only file durability logging and replay."""

import json
import os
from pathlib import Path
from typing import Any

from src.store import Store


class AOFLogger:
    """Persist mutation records as newline-delimited JSON."""

    def __init__(self, filepath: str | Path, fsync: bool = True) -> None:
        self.filepath = Path(filepath)
        self.fsync = fsync

    def log_mutation(self, record: dict[str, Any]) -> None:
        """Append one mutation and optionally force it to durable storage."""
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(record, separators=(",", ":")) + "\n"
        with self.filepath.open("a", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            if self.fsync:
                os.fsync(stream.fileno())

    def truncate(self) -> None:
        """Remove all records, without creating a previously absent AOF."""
        if self.filepath.exists():
            with self.filepath.open("w", encoding="utf-8"):
                pass


def _replay_record(record: Any, store: Store) -> bool:
    if not isinstance(record, dict):
        return False

    operation = record.get("op")
    try:
        if operation == "SET":
            key = record["key"]
            value = record["value"]
            store.set(key, value, expire_at=record.get("expire_at"))
            return True
        if operation == "DEL":
            store.delete(record["key"])
            return True
        if operation == "EXPIRE":
            key = record["key"]
            expire_at = record["expire_at"]
            if store.exists(key):
                store._expires[key] = expire_at
            return True
        if operation == "FLUSHALL":
            store.flushall()
            return True
    except (KeyError, TypeError, ValueError):
        return False
    return False


def replay_aof(filepath: str | Path, store: Store) -> int:
    """Replay valid newline-delimited mutations and return their count.

    A missing file, blank line, malformed JSON, malformed record, or unknown
    operation is ignored so a damaged trailing AOF cannot prevent startup.
    """
    path = Path(filepath)
    if not path.exists():
        return 0

    replayed = 0
    with path.open("r", encoding="utf-8") as stream:
        for raw_line in stream:
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if _replay_record(record, store):
                replayed += 1
    return replayed
