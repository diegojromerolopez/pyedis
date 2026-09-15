import unittest
from src.store import Store


class StoreTests(unittest.TestCase):
    def test_expiration_and_ttl(self) -> None:
        now = [10.0]
        store = Store(lambda: now[0])
        self.assertTrue(store.set("a", "b", 12.0))
        self.assertEqual(store.ttl("a"), 2)
        now[0] = 12.0
        self.assertIsNone(store.get("a"))
        self.assertEqual(store.ttl("a"), -2)

    def test_keys_sorted(self) -> None:
        store = Store(); store.set("b", "2"); store.set("a", "1")
        self.assertEqual(store.keys("*"), ["a", "b"])
