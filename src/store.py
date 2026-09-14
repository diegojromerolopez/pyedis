from __future__ import annotations

import asyncio
import fnmatch
import time
from collections.abc import Callable


class Store:
    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self.clock = clock
        self._values: dict[str, str] = {}
        self._expires: dict[str, float] = {}
        self.lock = asyncio.Lock()

    def _purge(self, key: str) -> None:
        expiry = self._expires.get(key)
        if expiry is not None and self.clock() >= expiry:
            self._values.pop(key, None)
            self._expires.pop(key, None)

    def _purge_all(self) -> None:
        for key in list(self._values):
            self._purge(key)

    async def get(self, key: str) -> str | None:
        async with self.lock:
            self._purge(key)
            return self._values.get(key)

    async def exists(self, key: str) -> bool:
        async with self.lock:
            self._purge(key)
            return key in self._values

    async def set(self, key: str, value: str, expire_at: float | None = None) -> None:
        async with self.lock:
            self._values[key] = value
            if expire_at is None:
                self._expires.pop(key, None)
            else:
                self._expires[key] = expire_at

    async def delete(self, *keys: str) -> int:
        async with self.lock:
            count = 0
            for key in keys:
                self._purge(key)
                if key in self._values:
                    count += 1
                    self._values.pop(key, None)
                    self._expires.pop(key, None)
            return count

    async def increment(self, key: str, amount: int = 1) -> tuple[int, bool]:
        async with self.lock:
            self._purge(key)
            old_expiry = self._expires.get(key)
            raw = self._values.get(key, "0")
            try:
                value = int(raw)
            except ValueError:
                return 0, False
            value += amount
            self._values[key] = str(value)
            if old_expiry is not None:
                self._expires[key] = old_expiry
            return value, True

    async def expire(self, key: str, seconds: int) -> bool:
        async with self.lock:
            self._purge(key)
            if key not in self._values:
                return False
            if seconds <= 0:
                self._values.pop(key, None)
                self._expires.pop(key, None)
            else:
                self._expires[key] = self.clock() + seconds
            return True

    async def ttl(self, key: str) -> int:
        async with self.lock:
            self._purge(key)
            if key not in self._values:
                return -2
            expiry = self._expires.get(key)
            if expiry is None:
                return -1
            return max(0, int(expiry - self.clock()))

    async def keys(self, pattern: str) -> list[str]:
        async with self.lock:
            self._purge_all()
            return sorted(key for key in self._values if fnmatch.fnmatchcase(key, pattern))

    async def flushall(self) -> None:
        async with self.lock:
            self._values.clear()
            self._expires.clear()

    async def snapshot(self) -> dict[str, tuple[str, float | None]]:
        async with self.lock:
            self._purge_all()
            return {key: (value, self._expires.get(key)) for key, value in self._values.items()}
