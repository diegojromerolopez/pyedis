import json
import os
import sys
from typing import Any
from src.store import Store


class AOFLogger:
    def __init__(self, data_dir: str, fsync: bool = True) -> None:
        self.data_dir = data_dir
        self.fsync = fsync
        os.makedirs(self.data_dir, exist_ok=True)
        self.filepath = os.path.join(self.data_dir, "dump.aof")
        self._file = open(self.filepath, "a+", encoding="utf-8")

    def append(self, record: dict[str, Any]) -> None:
        line = json.dumps(record) + "\n"
        self._file.write(line)
        self._file.flush()
        if self.fsync:
            os.fsync(self._file.fileno())

    def truncate(self) -> None:
        self._file.close()
        self._file = open(self.filepath, "w+", encoding="utf-8")

    def replay(self, store: Store) -> None:
        if not os.path.exists(self.filepath):
            return
        with open(self.filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                op = rec.get("op")
                if op == "SET":
                    store.set(rec["key"], rec["value"], rec.get("expire_at"))
                elif op == "DEL":
                    store.delete([rec["key"]])
                elif op == "INCR":
                    store.incr(rec["key"], 1)
                elif op == "DECR":
                    store.incr(rec["key"], -1)
                elif op == "EXPIRE":
                    store._expires[rec["key"]] = rec["expire_at"]
                elif op == "FLUSHALL":
                    store.flushall()
            except Exception:
                if idx == len(lines) - 1:
                    sys.stderr.write("pyedis: ignoring corrupt trailing AOF line\n")
                else:
                    raise

    def close(self) -> None:
        self._file.close()
