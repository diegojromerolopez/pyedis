from __future__ import annotations

import asyncio
import time
from typing import Callable


class Store:
    def __init__(self, time_func: Callable[[], float] = time.time) -> None:
        self._data: dict[str, str] = {}
        self._expires: dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._time_func = time_func

    def _check_expired(self, key: str) -> None:
        if key in self._expires:
            if self._time_func() >= self._expires[key]:
                self._data.pop(key, None)
                self._expires.pop(key, None)

    async def get(self, key: str) -> str | None:
        async with self._lock:
            self._check_expired(key)
            return self._data.get(key)

    async def set(
        self,
        key: str,
        val: str,
        ex: int | float | None = None,
        px: int | float | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        async with self._lock:
            self._check_expired(key)
            exists = key in self._data
            if nx and exists:
                return False
            if xx and not exists:
                return False

            self._data[key] = val
            now = self._time_func()
            if ex is not None:
                self._expires[key] = now + ex
            elif px is not None:
                self._expires[key] = now + (px / 1000.0)
            else:
                self._expires.pop(key, None)
            return True

    async def delete(self, *keys: str) -> int:
        async with self._lock:
            count = 0
            for k in keys:
                self._check_expired(k)
                if k in self._data:
                    del self._data[k]
                    self._expires.pop(k, None)
                    count += 1
            return count

    async def exists(self, *keys: str) -> int:
        async with self._lock:
            count = 0
            for k in keys:
                self._check_expired(k)
                if k in self._data:
                    count += 1
            return count

    async def incr_by(self, key: str, amount: int) -> tuple[int | None, str | None]:
        async with self._lock:
            self._check_expired(key)
            if key in self._data:
                val_str = self._data[key]
                try:
                    val_int = int(val_str)
                except ValueError:
                    return None, "ERR value is not an integer or out of range"
            else:
                val_int = 0

            new_val = val_int + amount
            self._data[key] = str(new_val)
            return new_val, None
