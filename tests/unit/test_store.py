import unittest
from src.store import Store

class StoreTest(unittest.TestCase):
    def test_values_and_expiry(self) -> None:
        now = [10.0]; store = Store(lambda: now[0]); store.set(b"a", b"b", 12.0)
        self.assertEqual(store.get(b"a"), b"b"); self.assertEqual(store.ttl(b"a"), 2)
        now[0] = 13.0; self.assertIsNone(store.get(b"a")); self.assertEqual(store.ttl(b"a"), -2)

    def test_keys(self) -> None:
        store = Store(); store.set(b"abc", b"1"); store.set(b"abd", b"2")
        self.assertEqual(store.keys(b"ab?"), [b"abc", b"abd"])
