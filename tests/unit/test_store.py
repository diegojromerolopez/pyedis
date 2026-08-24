import asyncio
import unittest

from src.store import Store


class TestStore(unittest.IsolatedAsyncioTestCase):
    async def test_get_and_set(self) -> None:
        store = Store()
        self.assertIsNone(await store.get("k1"))
        await store.set("k1", "v1")
        self.assertEqual(await store.get("k1"), "v1")

    async def test_exists(self) -> None:
        store = Store()
        await store.set("k1", "v1")
        await store.set("k2", "v2")
        self.assertEqual(await store.exists("k1"), 1)
        self.assertEqual(await store.exists("k1", "k2", "k3"), 2)

    async def test_delete(self) -> None:
        store = Store()
        await store.set("k1", "v1")
        await store.set("k2", "v2")
        deleted = await store.delete("k1", "k3")
        self.assertEqual(deleted, 1)
        self.assertIsNone(await store.get("k1"))
        self.assertEqual(await store.get("k2"), "v2")

    async def test_concurrency_lock_behavior(self) -> None:
        store = Store()

        async def task(i: int) -> None:
            await store.set(f"key_{i}", f"val_{i}")
            val = await store.get(f"key_{i}")
            self.assertEqual(val, f"val_{i}")

        tasks = [task(i) for i in range(50)]
        await asyncio.gather(*tasks)

        exists_count = await store.exists(*[f"key_{i}" for i in range(50)])
        self.assertEqual(exists_count, 50)


if __name__ == "__main__":
    unittest.main()
