import asyncio
import fnmatch
import time
from collections.abc import Callable
from typing import Any


class Store:
    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self._data: dict[str, bytes] = {}
        self._expires: dict[str, float] = {}
        self._clock = clock
        self.lock = asyncio.Lock()

    def _now(self) -> float:
        return self._clock()

    def _purge_if_expired(self, key: str) -> bool:
        if key in self._expires:
            if self._now() >= self._expires[key]:
                del self._expires[key]
                if key in self._data:
                    del self._data[key]
                return True
        return False

    def get(self, key: str) -> bytes | None:
        if self._purge_if_expired(key):
            return None
        return self._data.get(key)

    def set(self, key: str, value: bytes, expire_at: float | None = None) -> None:
        self._data[key] = value
        if expire_at is not None:
            self._expires[key] = expire_at
        else:
            self._expires.pop(key, None)

    def delete(self, keys: list[str]) -> int:
        count = 0
        for k in keys:
            self._purge_if_expired(k)
            in_data = k in self._data
            in_exp = k in self._expires
            self._data.pop(k, None)
            self._expires.pop(k, None)
            if in_data or in_exp:
                count += 1
        return count

    def exists(self, keys: list[str]) -> int:
        count = 0
        for k in keys:
            if not self._purge_if_expired(k) and k in self._data:
                count += 1
        return count

    def expire(self, key: str, expire_at: float) -> bool:
        if self._purge_if_expired(key) or key not in self._data:
            return False
        self._expires[key] = expire_at
        return True

    def ttl(self, key: str) -> int:
        if self._purge_if_expired(key) or key not in self._data:
            return -2
        if key not in self._expires:
            return -1
        remaining = int(self._expires[key] - self._now())
        return remaining if remaining >= 0 else -2

    def active_sweep(self) -> None:
        now = self._now()
        expired_keys = [k for k, exp in self._expires.items() if now >= exp]
        for k in expired_keys:
            self._expires.pop(k, None)
            self._data.pop(k, None)

    def keys(self, pattern: str) -> list[str]:
        self.active_sweep()
        res: list[str] = []
        for k in self._data.keys():
            if fnmatch.fnmatch(k, pattern):
                res.append(k)
        return res

    def flushall(self) -> None:
        self._data.clear()
        self._expires.clear()

    def incrby(self, key: str, amount: int) -> int:
        self._purge_if_expired(key)
        val_bytes = self._data.get(key, b"0")
        try:
            val_int = int(val_bytes.decode("utf-8"))
        except ValueError:
            raise ValueError("value is not an integer or out of range")
        val_int += amount
        self._data[key] = str(val_int).encode("utf-8")
        return val_int
