"""In-memory store operations tests."""

import unittest
from src.store import Store


class TestStore(unittest.TestCase):
    def setUp(self) -> None:
        self.current_time = 1000.0
        self.store = Store(clock=lambda: self.current_time)

    def test_set_and_get(self) -> None:
        self.store.set("k1", "v1")
        self.assertEqual(self.store.get("k1"), "v1")

    def test_missing_key_and_overwrite(self) -> None:
        self.assertIsNone(self.store.get("missing"))
        self.assertTrue(self.store.set("k1", "v1"))
        self.assertTrue(self.store.set("k1", "v2"))
        self.assertEqual(self.store.get("k1"), "v2")

    def test_delete_and_exists(self) -> None:
        self.store.set("k1", "v1")
        self.store.set("k2", "v2")
        self.assertEqual(self.store.exists("k1"), 1)
        self.assertEqual(self.store.exists("k1", "missing", "k2"), 2)
        self.assertEqual(self.store.delete("k1"), 1)
        self.assertEqual(self.store.delete("k1", "missing"), 0)
        self.assertEqual(self.store.exists("k1"), 0)
        self.assertEqual(self.store.get("k2"), "v2")

    def test_expiration(self) -> None:
        self.store.set("k1", "v1", expire_at=1005.0)
        self.assertEqual(self.store.get("k1"), "v1")
        self.current_time = 1005.0
        self.assertIsNone(self.store.get("k1"))
        self.store.set("k1", "v1", expire_at=1005.0)
        self.current_time = 1006.0
        self.assertIsNone(self.store.get("k1"))

    def test_expiration_is_lazy_for_exists_and_delete(self) -> None:
        self.store.set("k1", "v1", expire_at=1005.0)
        self.current_time = 1005.0
        self.assertEqual(self.store.exists("k1"), 0)
        self.assertEqual(self.store.delete("k1"), 0)

    def test_lock_is_exposed_as_asyncio_lock(self) -> None:
        import asyncio

        self.assertIsInstance(self.store.lock, asyncio.Lock)
        self.assertIs(self.store.lock, self.store.lock)

    def test_incr_decr(self) -> None:
        self.assertEqual(self.store.incr_by("counter", 1), 1)
        self.assertEqual(self.store.incr_by("counter", 5), 6)
        self.assertEqual(self.store.incr_by("counter", -2), 4)


if __name__ == "__main__":
    unittest.main()
