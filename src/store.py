"""In-memory key-value storage with active/lazy expiration and injected clock."""

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
        self._hll: dict[str, set[str]] = {}
        self._expires: dict[str, float] = {}
        self._clock: Clock = clock
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock

    def _is_expired(self, key: str) -> bool:
        if key in self._expires:
            if self._clock() >= self._expires[key]:
                self._delete_internal(key)
                return True
        return False

    def _delete_internal(self, key: str) -> bool:
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
        if key in self._hll:
            del self._hll[key]
            existed = True
        if key in self._expires:
            del self._expires[key]
            existed = True
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
        self._delete_internal(key)
        self._strings[key] = value
        if expire_at is not None:
            self._expires[key] = expire_at
        return True

    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            self._is_expired(k)
            if self._delete_internal(k):
                count += 1
        return count

    def exists(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if not self._is_expired(k):
                if (
                    k in self._strings
                    or k in self._lists
                    or k in self._hashes
                    or k in self._sets
                    or k in self._zsets
                    or k in self._hll
                ):
                    count += 1
        return count

    def incr_by(self, key: str, delta: int) -> int:
        if self._is_expired(key):
            val = 0
        else:
            val_str = self._strings.get(key, "0")
            try:
                val = int(val_str)
            except ValueError:
                raise ValueError("value is not an integer or out of range") from None
        new_val = val + delta
        self._strings[key] = str(new_val)
        return new_val

    def expire(self, key: str, seconds: float) -> bool:
        if self._is_expired(key):
            return False
        if not self.exists(key):
            return False
        if seconds <= 0:
            self._delete_internal(key)
            return True
        self._expires[key] = self._clock() + seconds
        return True

    def ttl(self, key: str) -> int:
        if self._is_expired(key) or not self.exists(key):
            return -2
        if key not in self._expires:
            return -1
        remaining = int(self._expires[key] - self._clock())
        return remaining if remaining >= 0 else -2

    def keys(self, pattern: str) -> list[str]:
        all_keys = list(
            set(
                list(self._strings.keys())
                + list(self._lists.keys())
                + list(self._hashes.keys())
                + list(self._sets.keys())
                + list(self._zsets.keys())
                + list(self._hll.keys())
            )
        )
        active_keys = [k for k in all_keys if not self._is_expired(k)]
        return fnmatch.filter(active_keys, pattern)

    def flushall(self) -> None:
        self._strings.clear()
        self._lists.clear()
        self._hashes.clear()
        self._sets.clear()
        self._zsets.clear()
        self._hll.clear()
        self._expires.clear()
