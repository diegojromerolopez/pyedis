"""In-memory key-value storage with active/lazy expiration and DI clock."""

import asyncio
import fnmatch
import time
from collections.abc import Callable
from typing import Any

Clock = Callable[[], float]


class Store:
    def __init__(self, clock: Clock = time.time) -> None:
        self._strings: dict[str, str] = {}
        self._lists: dict[str, list[str]] = {}
        self._hashes: dict[str, dict[str, str]] = {}
        self._sets: dict[str, set[str]] = {}
        self._zsets: dict[str, dict[str, float]] = {}
        self._expires: dict[str, float] = {}
        self._clock: Clock = clock
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock

    def _is_expired(self, key: str) -> bool:
        if key in self._expires:
            if self._clock() >= self._expires[key]:
                self._delete_key(key)
                return True
        return False

    def _delete_key(self, key: str) -> bool:
        existed = False
        if key in self._strings:
            del self._strings[key]
            existed = True
        if key in self._lists:
            del self._lists[key]
            existed = True
        if key in self._hashes:
            del self._hashes[key]
            existed = True
        if key in self._sets:
            del self._sets[key]
            existed = True
        if key in self._zsets:
            del self._zsets[key]
            existed = True
        self._expires.pop(key, None)
        return existed

    def get(self, key: str) -> str | None:
        if self._is_expired(key):
            return None
        return self._strings.get(key)

    def set(
        self,
        key: str,
        value: str,
        expire_at: float | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        self._is_expired(key)
        exists = key in self._strings
        if nx and exists:
            return False
        if xx and not exists:
            return False
        self._strings[key] = value
        if expire_at is not None:
            self._expires[key] = expire_at
        else:
            self._expires.pop(key, None)
        return True

    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            self._is_expired(k)
            if self._delete_key(k):
                count += 1
        return count

    def exists(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if not self._is_expired(k):
                if any(
                    k in d
                    for d in (self._strings, self._lists, self._hashes, self._sets, self._zsets)
                ):
                    count += 1
        return count

    def incr_by(self, key: str, delta: int) -> int:
        self._is_expired(key)
        val_str = self._strings.get(key, "0")
        try:
            val = int(val_str)
        except ValueError:
            raise ValueError("ERR value is not an integer or out of range")
        new_val = val + delta
        self._strings[key] = str(new_val)
        return new_val

    def expire(self, key: str, seconds: float) -> bool:
        if self._is_expired(key):
            return False
        if not self.exists(key):
            return False
        if seconds <= 0:
            self._delete_key(key)
            return True
        self._expires[key] = self._clock() + seconds
        return True

    def ttl(self, key: str) -> int:
        if self._is_expired(key):
            return -2
        if not self.exists(key):
            return -2
        if key not in self._expires:
            return -1
        remaining = int(self._expires[key] - self._clock())
        return remaining if remaining >= 0 else -2

    def keys(self, pattern: str) -> list[str]:
        # Active sweep
        now = self._clock()
        expired = [k for k, exp in self._expires.items() if now >= exp]
        for k in expired:
            self._delete_key(k)

        all_keys = set()
        for d in (self._strings, self._lists, self._hashes, self._sets, self._zsets):
            all_keys.update(d.keys())
        return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]

    def flushall(self) -> None:
        self._strings.clear()
        self._lists.clear()
        self._hashes.clear()
        self._sets.clear()
        self._zsets.clear()
        self._expires.clear()
