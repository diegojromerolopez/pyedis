from __future__ import annotations

import asyncio
from typing import Dict, Optional


class Store:
    def __init__(self) -> None:
        self._data: Dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            return self._data.get(key)

    async def set(self, key: str, val: str) -> None:
        async with self._lock:
            self._data[key] = val

    async def delete(self, *keys: str) -> int:
        async with self._lock:
            count = 0
            for k in keys:
                if k in self._data:
                    del self._data[k]
                    count += 1
            return count

    async def exists(self, *keys: str) -> int:
        async with self._lock:
            count = 0
            for k in keys:
                if k in self._data:
                    count += 1
            return count
