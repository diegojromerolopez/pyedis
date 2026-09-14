"""Append-only JSON persistence."""
from __future__ import annotations
import json
import os
import sys
from typing import Any
from .store import Store

class AOF:
    def __init__(self, path: str, fsync: bool = True) -> None:
        self.path = path; self.fsync = fsync
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        self.file = open(path, 'a+', encoding='utf-8')

    def append(self, record: dict[str, Any]) -> None:
        self.file.write(json.dumps(record, separators=(',', ':')) + '\n'); self.file.flush()
        if self.fsync: os.fsync(self.file.fileno())

    def truncate(self) -> None:
        self.file.seek(0); self.file.truncate(); self.file.flush()
        if self.fsync: os.fsync(self.file.fileno())

    def close(self) -> None: self.file.close()

    async def replay(self, store: Store) -> None:
        try: lines = open(self.path, encoding='utf-8').readlines()
        except FileNotFoundError: return
        for line in lines:
            try:
                item = json.loads(line); op = item['op']
                if op == 'SET': await store.set(item['key'], item['value'], item.get('expire_at'))
                elif op == 'DEL': await store.delete([item['key']])
                elif op in ('INCR', 'DECR'): await store.increment(item['key'], 1 if op == 'INCR' else -1)
                elif op == 'EXPIRE':
                    async with store.lock:
                        store._purge(item['key'])
                        if item['key'] in store.values: store.expirations[item['key']] = float(item['expire_at'])
                elif op == 'FLUSHALL': await store.flush()
            except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                print('pyedis: ignoring corrupt trailing AOF line', file=sys.stderr)
