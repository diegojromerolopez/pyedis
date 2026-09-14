import json
import os
import sys
from typing import Any

from src.store import Store


class AOFLogger:
    def __init__(self, data_dir: str, fsync: bool = True) -> None:
        self.data_dir = data_dir
        self.fsync = fsync
        os.makedirs(data_dir, exist_ok=True)
        self.filepath = os.path.join(data_dir, "dump.aof")
        self.file = open(self.filepath, "a+", encoding="utf-8")

    def log(self, entry: dict[str, Any]) -> None:
        line = json.dumps(entry) + "\n"
        self.file.write(line)
        self.file.flush()
        if self.fsync:
            os.fsync(self.file.fileno())

    def truncate(self) -> None:
        self.file.close()
        self.file = open(self.filepath, "w+", encoding="utf-8")
        self.file.flush()
        if self.fsync:
            os.fsync(self.file.fileno())

    def replay(self, store: Store) -> None:
        if not os.path.exists(self.filepath):
            return
        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    sys.stderr.write("pyedis: ignoring corrupt trailing AOF line\n")
                    break
                op = rec.get("op")
                if op == "SET":
                    val = (
                        rec["value"].encode("utf-8")
                        if isinstance(rec["value"], str)
                        else rec["value"]
                    )
                    store.set(rec["key"], val, rec.get("expire_at"))
                elif op == "DEL":
                    store.delete([rec["key"]])
                elif op == "INCR":
                    try:
                        store.incrby(rec["key"], 1)
                    except ValueError:
                        pass
                elif op == "DECR":
                    try:
                        store.incrby(rec["key"], -1)
                    except ValueError:
                        pass
                elif op == "EXPIRE":
                    store.expire(rec["key"], rec["expire_at"])
                elif op == "FLUSHALL":
                    store.flushall()
