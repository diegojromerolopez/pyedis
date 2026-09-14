import asyncio
import unittest
from src.store import Store


class StoreTests(unittest.IsolatedAsyncioTestCase):
    async def test_expiration(self) -> None:
        now = [100.0]
        store = Store(lambda: now[0])
        await store.set("k", b"v", 105.0)
        self.assertEqual(await store.ttl("k"), 5)
        now[0] = 106
        self.assertIsNone(await store.get("k"))
        self.assertEqual(await store.ttl("k"), -2)

    async def test_increment_and_keys(self) -> None:
        store = Store()
        self.assertEqual(await store.increment("n", 1), 1)
        self.assertEqual(await store.keys("*"), ["n"])


if __name__ == "__main__":
    unittest.main()
