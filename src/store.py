"""In-memory key/value store with expirations."""
from __future__ import annotations

import fnmatch
import time
from dataclasses import dataclass

@dataclass
class Entry:
    value: bytes
    expire_at: float | None = None

class Store:
    def __init__(self, clock: callable = time.time) -> None:
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

    def keys(self, pattern: bytes = b'*') -> list[bytes]:
        for key in list(self.data):
            self._expired(key)
        return sorted(k for k in self.data if fnmatch.fnmatchcase(k.decode(errors='surrogateescape'), pattern.decode(errors='surrogateescape')))

    def clear(self) -> None:
        for key in list(self.data):
            self._expired(key)
        self.data.clear()
