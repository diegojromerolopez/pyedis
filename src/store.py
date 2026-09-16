"""Concurrent in-memory store with absolute expirations."""

from __future__ import annotations

import asyncio
import fnmatch
import time
from collections.abc import Callable


class Store:
    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self.clock = clock
        self.values: dict[str, str] = {}
        self.expirations: dict[str, float] = {}
        self.lock = asyncio.Lock()

    def _purge(self, key: str) -> None:
        expiry = self.expirations.get(key)
        if expiry is not None and self.clock() >= expiry:
            self.values.pop(key, None)
            self.expirations.pop(key, None)

    def _sweep(self) -> None:
        for key in list(self.values):
            self._purge(key)

    async def get(self, key: str) -> str | None:
        async with self.lock:
            self._purge(key)
            return self.values.get(key)

    async def exists(self, key: str) -> bool:
        async with self.lock:
            self._purge(key)
            return key in self.values

    async def set(
        self, key: str, value: str, expire_at: float | None = None, nx: bool = False, xx: bool = False
    ) -> bool:
        async with self.lock:
            self._purge(key)
            present = key in self.values
            if (nx and present) or (xx and not present):
                return False
            self.values[key] = value
            self.expirations.pop(key, None)
            if expire_at is not None:
                self.expirations[key] = expire_at
            return True

    async def delete(self, keys: list[str]) -> int:
        async with self.lock:
            count = 0
            for key in keys:
                self._purge(key)
                if key in self.values:
                    count += 1
                    self.values.pop(key)
                    self.expirations.pop(key, None)
            return count

    async def number(self, key: str, amount: int) -> int:
        result = await self.incr(key, amount)
        if result is None:
            raise ValueError("value is not an integer")
        return result[0]

    async def incr(self, key: str, amount: int) -> tuple[int, float | None] | None:
        async with self.lock:
            self._purge(key)
            old_expiry = self.expirations.get(key)
            raw = self.values.get(key, "0")
            try:
                value = int(raw) + amount
            except ValueError:
                return None
            self.values[key] = str(value)
            if old_expiry is not None:
                self.expirations[key] = old_expiry
            return value, old_expiry

    async def expire(self, key: str, seconds: int) -> bool:
        async with self.lock:
            self._purge(key)
            if key not in self.values:
                return False
            if seconds <= 0:
                self.values.pop(key)
                self.expirations.pop(key, None)
            else:
                self.expirations[key] = self.clock() + seconds
            return True

    async def ttl(self, key: str) -> int:
        async with self.lock:
            self._purge(key)
            if key not in self.values:
                return -2
            expiry = self.expirations.get(key)
            if expiry is None:
                return -1
            return max(0, int(expiry - self.clock()))

    async def keys(self, pattern: str) -> list[str]:
        async with self.lock:
            self._sweep()
            return sorted(key for key in self.values if fnmatch.fnmatchcase(key, pattern))

    async def flush(self) -> None:
        async with self.lock:
            self.values.clear()
            self.expirations.clear()
