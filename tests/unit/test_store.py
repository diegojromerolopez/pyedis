import asyncio
import unittest
from src.store import Store


class StoreTests(unittest.IsolatedAsyncioTestCase):
    async def test_expiration(self) -> None:
        now = [100.0]
        store = Store(lambda: now[0])
        await store.set("key", b"value", 105.0)
        self.assertEqual(await store.ttl("key"), 5)
        now[0] = 106.0
        self.assertIsNone(await store.get("key"))
        self.assertEqual(await store.ttl("key"), -2)

    async def test_counter_and_keys(self) -> None:
        store = Store()
        self.assertEqual(await store.number("n", 1), 1)
        self.assertEqual(await store.number("n", 1), 2)
        self.assertEqual(await store.keys("*"), ["n"])
