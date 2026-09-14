import asyncio
import unittest
from src.store import Store


class StoreTests(unittest.TestCase):
    def test_expiration_and_overwrite(self) -> None:
        now = [100.0]
        store = Store(lambda: now[0])
        asyncio.run(store.set("k", b"v", 105.0))
        self.assertEqual(asyncio.run(store.ttl("k")), 5)
        now[0] = 106
        self.assertIsNone(asyncio.run(store.get("k")))
        asyncio.run(store.set("k", b"v", 200))
        asyncio.run(store.set("k", b"new"))
        self.assertEqual(asyncio.run(store.ttl("k")), -1)
