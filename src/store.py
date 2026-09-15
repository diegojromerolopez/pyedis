"""In-memory key-value store."""
from __future__ import annotations

import fnmatch
import time
from dataclasses import dataclass
from collections.abc import Callable


@dataclass
class Entry:
    value: str
    expire_at: float | None = None


class Store:
    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self.clock = clock
        self.items: dict[str, Entry] = {}

    def _expired(self, key: str) -> bool:
        item = self.items.get(key)
        if item is not None and item.expire_at is not None and item.expire_at <= self.clock():
            del self.items[key]
            return True
        return item is None

    def get(self, key: str) -> Entry | None:
        self._expired(key)
        return self.items.get(key)

    def set(self, key: str, value: str, expire_at: float | None = None, condition: str | None = None) -> bool:
        exists = self.get(key) is not None
        if condition == "NX" and exists or condition == "XX" and not exists:
            return False
        self.items[key] = Entry(value, expire_at)
        return True

    def delete(self, keys: list[str]) -> int:
        count = 0
        for key in keys:
            if self.get(key) is not None:
                del self.items[key]
                count += 1
        return count

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def expire(self, key: str, seconds: int) -> bool:
        item = self.get(key)
        if item is None:
            return False
        if seconds <= 0:
            del self.items[key]
        else:
            item.expire_at = self.clock() + seconds
        return True

    def ttl(self, key: str) -> int:
        item = self.get(key)
        if item is None:
            return -2
        if item.expire_at is None:
            return -1
        return max(0, int(item.expire_at - self.clock()))

    def keys(self, pattern: str) -> list[str]:
        for key in list(self.items):
            self._expired(key)
        return sorted(key for key in self.items if fnmatch.fnmatchcase(key, pattern))

    def flush(self) -> None:
        self.items.clear()
