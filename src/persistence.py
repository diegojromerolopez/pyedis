""" append-only JSON persistence."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

class AOF:
    def __init__(self, directory: str, fsync: bool = True, clock: callable | None = None) -> None:
        self.path = Path(directory) / 'dump.aof'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fsync = fsync
        self.clock = clock

    def append(self, record: dict[str, Any]) -> None:
        with self.path.open('ab') as handle:
            handle.write(json.dumps(record, separators=(',', ':')).encode() + b'\n')
            handle.flush()
            if self.fsync:
                os.fsync(handle.fileno())

    def truncate(self) -> None:
        self.path.write_bytes(b'')

    def load(self, store: Any) -> None:
        if not self.path.exists():
            return
        lines = self.path.read_bytes().splitlines()
        for number, raw in enumerate(lines):
            try:
                item = json.loads(raw)
                op = item['op']
                if op == 'SET':
                    expiry = item.get('expire_at')
                    if expiry is None or self.clock is None or expiry > self.clock():
                        store.set(item['key'].encode(), item['value'].encode(), expiry)
                elif op == 'DEL':
                    store.delete(item['key'].encode())
                elif op in ('INCR', 'DECR'):
                    key = item['key'].encode(); old = store.get(key)
                    value = int(old or b'0') + (1 if op == 'INCR' else -1)
                    store.set(key, str(value).encode())
                elif op == 'EXPIRE':
                    key = item['key'].encode()
                    if store.get(key) is not None:
                        store.data[key].expire_at = item['expire_at']
                elif op == 'FLUSHALL':
                    store.clear()
            except Exception as exc:
                if number == len(lines) - 1:
                    print('pyedis: ignoring corrupt trailing AOF line')
                    return
                raise RuntimeError(f'corrupt AOF line {number + 1}') from exc
