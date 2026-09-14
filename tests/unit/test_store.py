import unittest
from src.store import Store


class TestStore(unittest.TestCase):
    def setUp(self) -> None:
        self.time = 1000.0
        self.store = Store(clock=lambda: self.time)

    def test_set_get_del(self) -> None:
        self.store.set("k1", "v1")
        self.assertEqual(self.store.get("k1"), "v1")
        self.assertEqual(self.store.delete(["k1"]), 1)
        self.assertIsNone(self.store.get("k1"))

    def test_expiration(self) -> None:
        self.store.set("k1", "v1", expire_at=1005.0)
        self.assertEqual(self.store.ttl("k1"), 5)
        self.time = 1006.0
        self.assertIsNone(self.store.get("k1"))
        self.assertEqual(self.store.ttl("k1"), -2)


if __name__ == "__main__":
    unittest.main()
