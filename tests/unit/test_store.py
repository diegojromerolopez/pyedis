"""Unit tests for the in-memory store."""

import unittest

from src.store import Store
from tests.doubles import MutableClock


class TestStore(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = MutableClock(1000.0)
        self.store = Store(clock=self.clock)

    def test_set_get_delete_and_exists(self) -> None:
        self.assertTrue(self.store.set("k1", "v1"))
        self.assertEqual(self.store.get("k1"), "v1")
        self.assertEqual(self.store.exists("k1", "missing"), 1)
        self.assertEqual(self.store.delete("k1", "missing"), 1)
        self.assertIsNone(self.store.get("k1"))
        self.assertEqual(self.store.exists("k1"), 0)

    def test_conditional_set(self) -> None:
        self.assertTrue(self.store.set("key", "first", nx=True))
        self.assertFalse(self.store.set("key", "second", nx=True))
        self.assertFalse(self.store.set("new", "value", xx=True))
        self.assertTrue(self.store.set("key", "second", xx=True))
        self.assertEqual(self.store.get("key"), "second")

    def test_expiration_is_lazy_and_boundary_is_inclusive(self) -> None:
        self.store.set("key", "value", expire_at=1005.0)
        self.clock.value = 1004.99
        self.assertEqual(self.store.get("key"), "value")
        self.clock.value = 1005.0
        self.assertIsNone(self.store.get("key"))
        self.assertEqual(self.store.exists("key"), 0)

    def test_expire_and_ttl(self) -> None:
        self.store.set("key", "value")
        self.assertEqual(self.store.ttl("key"), -1)
        self.assertTrue(self.store.expire("key", 10))
        self.assertEqual(self.store.ttl("key"), 10)
        self.clock.advance(3.2)
        self.assertEqual(self.store.ttl("key"), 6)
        self.assertTrue(self.store.expire("key", 0))
        self.assertEqual(self.store.ttl("key"), -2)
        self.assertFalse(self.store.expire("missing", 1))

    def test_keys_pattern_and_flushall(self) -> None:
        self.store.set("user:1", "a")
        self.store.set("user:2", "b")
        self.store.set("other", "c")
        self.assertCountEqual(self.store.keys("user:*"), ["user:1", "user:2"])
        self.store.flushall()
        self.assertEqual(self.store.keys("*"), [])
        self.assertEqual(self.store.exists("user:1", "other"), 0)

    def test_increment_and_non_integer_error(self) -> None:
        self.assertEqual(self.store.incr_by("counter", 2), 2)
        self.assertEqual(self.store.get("counter"), "2")
        self.store.set("text", "nope")
        with self.assertRaisesRegex(ValueError, "not an integer"):
            self.store.incr_by("text", 1)


if __name__ == "__main__":
    unittest.main()
