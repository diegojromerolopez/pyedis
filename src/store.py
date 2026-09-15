"""Expiring in-memory key-value store."""
from __future__ import annotations

import fnmatch
import time
from dataclasses import dataclass
from collections.abc import Callable


@dataclass
class Entry:
    value: bytes
    expire_at: float | None = None


class Store:
    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self.clock = clock
        self.data: dict[bytes, Entry] = {}

    def _expired(self, key: bytes) -> bool:
        entry = self.data.get(key)
        if entry is not None and entry.expire_at is not None and entry.expire_at <= self.clock():
            del self.data[key]
            return True
        return entry is None

    def get(self, key: bytes) -> bytes | None:
        return None if self._expired(key) else self.data[key].value

    def set(self, key: bytes, value: bytes, expire_at: float | None = None) -> None:
        self.data[key] = Entry(value, expire_at)

    def delete(self, key: bytes) -> bool:
        if self._expired(key):
            return False
        del self.data[key]
        return True

    def exists(self, key: bytes) -> bool:
        return not self._expired(key)

    def sweep(self) -> None:
        for key in list(self.data):
            self._expired(key)

    def keys(self, pattern: bytes) -> list[bytes]:
        self.sweep()
        expression = pattern.decode("latin1")
        return sorted((key for key in self.data if fnmatch.fnmatchcase(key.decode("latin1"), expression)))

    def ttl(self, key: bytes) -> int:
        if self._expired(key):
            return -2
        expiry = self.data[key].expire_at
        if expiry is None:
            return -1
        return max(0, int(expiry - self.clock()))
