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

    def test_expiration(self) -> None:
        self.store.set("k1", "v1", expire_at=1005.0)
        self.assertEqual(self.store.get("k1"), "v1")
        self.current_time = 1006.0
        self.assertIsNone(self.store.get("k1"))

    def test_incr_decr(self) -> None:
        self.assertEqual(self.store.incr_by("counter", 1), 1)
        self.assertEqual(self.store.incr_by("counter", 5), 6)
        self.assertEqual(self.store.incr_by("counter", -2), 4)

if __name__ == "__main__":
    unittest.main()
