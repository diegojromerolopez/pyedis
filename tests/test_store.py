import asyncio
import unittest
from src.store import Store


class StoreTest(unittest.IsolatedAsyncioTestCase):
    async def test_expiration_with_clock(self) -> None:
        now = [100.0]
        store = Store(lambda: now[0])
        await store.set("key", "value", 105.0)
        self.assertEqual(await store.ttl("key"), 5)
        now[0] = 106.0
        self.assertIsNone(await store.get("key"))
        self.assertEqual(await store.ttl("key"), -2)

    async def test_increment_and_delete(self) -> None:
        store = Store()
        self.assertEqual((await store.incr("n", 1))[0], 1)
        self.assertEqual(await store.delete(["n", "missing"]), 1)
