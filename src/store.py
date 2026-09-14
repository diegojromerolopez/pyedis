import asyncio
import fnmatch
import time
from typing import Callable


class Store:
    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self._clock = clock
        self._data: dict[str, str] = {}
        self._expires: dict[str, float] = {}
        self.lock = asyncio.Lock()

    def _is_expired(self, key: str) -> bool:
        if key in self._expires:
            if self._clock() >= self._expires[key]:
                self._purge(key)
                return True
        return False

    def _purge(self, key: str) -> None:
        self._data.pop(key, None)
        self._expires.pop(key, None)

    def get(self, key: str) -> str | None:
        if self._is_expired(key):
            return None
        return self._data.get(key)

    def set(self, key: str, value: str, expire_at: float | None = None) -> None:
        self._data[key] = value
        if expire_at is not None:
            self._expires[key] = expire_at
        else:
            self._expires.pop(key, None)

    def delete(self, keys: list[str]) -> int:
        count = 0
        for k in keys:
            self._is_expired(k)
            if k in self._data:
                self._purge(k)
                count += 1
        return count

    def exists(self, keys: list[str]) -> int:
        count = 0
        for k in keys:
            if not self._is_expired(k) and k in self._data:
                count += 1
        return count

    def incr(self, key: str, delta: int = 1) -> int:
        if self._is_expired(key):
            val = 0
        else:
            raw = self._data.get(key, "0")
            try:
                val = int(raw)
            except ValueError:
                raise ValueError("value is not an integer or out of range")
        val += delta
        self._data[key] = str(val)
        return val

    def expire(self, key: str, seconds: float) -> int:
        if self._is_expired(key) or key not in self._data:
            return 0
        if seconds <= 0:
            self._purge(key)
            return 1
        self._expires[key] = self._clock() + seconds
        return 1

    def ttl(self, key: str) -> int:
        if self._is_expired(key) or key not in self._data:
            return -2
        if key not in self._expires:
            return -1
        remaining = int(self._expires[key] - self._clock())
        return remaining if remaining >= 0 else -2

    def keys(self, pattern: str) -> list[str]:
        all_keys = list(self._data.keys())
        for k in all_keys:
            self._is_expired(k)
        return [k for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]

    def flushall(self) -> None:
        self._data.clear()
        self._expires.clear()
