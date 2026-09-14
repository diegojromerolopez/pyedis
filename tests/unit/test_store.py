import unittest
from src.store import Store


class TestStore(unittest.TestCase):
    def setUp(self) -> None:
        self.time = 100.0
        self.store = Store(clock=lambda: self.time)

    def test_set_get_ttl(self) -> None:
        self.store.set("k1", b"v1", expire_at=105.0)
        self.assertEqual(self.store.get("k1"), b"v1")
        self.assertEqual(self.store.ttl("k1"), 5)
        self.time = 106.0
        self.assertIsNone(self.store.get("k1"))
        self.assertEqual(self.store.ttl("k1"), -2)

    def test_incrby(self) -> None:
        res = self.store.incrby("num", 1)
        self.assertEqual(res, 1)
        res = self.store.incrby("num", 5)
        self.assertEqual(res, 6)
        self.assertEqual(self.store.get("num"), b"6")

    def test_keys_active_sweep(self) -> None:
        self.store.set("a", b"1")
        self.store.set("b", b"2", expire_at=102.0)
        self.time = 103.0
        self.assertEqual(self.store.keys("*"), ["a"])


if __name__ == "__main__":
    unittest.main()
