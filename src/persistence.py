from __future__ import annotations

import json
import os
import sys
from typing import Any

from .store import Store


class AOF:
    def __init__(self, path: str, fsync: bool = True) -> None:
        self.path = path
        self.do_fsync = fsync
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.file = open(path, "a+", encoding="utf-8")

    def append(self, record: dict[str, Any]) -> None:
        self.file.write(json.dumps(record, separators=(",", ":")) + "\n")
        self.file.flush()
        if self.do_fsync:
            os.fsync(self.file.fileno())

    def truncate(self) -> None:
        self.file.seek(0)
        self.file.truncate()
        self.file.flush()
        if self.do_fsync:
            os.fsync(self.file.fileno())

    def replay(self, store: Store) -> None:
        self.file.flush()
        try:
            lines = open(self.path, encoding="utf-8").read().splitlines()
        except OSError:
            return
        for line in lines:
            try:
                record = json.loads(line)
                op = record["op"]
                if op == "SET":
                    import asyncio

                    asyncio.run(
                        store.set(record["key"], record["value"].encode(), record.get("expire_at"))
                    )
                elif op == "DEL":
                    import asyncio

                    asyncio.run(store.delete([record["key"]]))
                elif op in ("INCR", "DECR"):
                    import asyncio

                    asyncio.run(store.increment(record["key"], 1 if op == "INCR" else -1))
                elif op == "EXPIRE":
                    import asyncio

                    asyncio.run(
                        store.set(record["key"], store.values[record["key"]], record["expire_at"])
                    )
                elif op == "FLUSHALL":
                    import asyncio

                    asyncio.run(store.flush())
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                print("pyedis: ignoring corrupt trailing AOF line", file=sys.stderr)
                break

    def close(self) -> None:
        self.file.close()
