<<<<<<< HEAD
"""Characterization tests for the in-memory store."""

import asyncio
=======
"""In-memory store operations tests."""

<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> noctifab/task-US-001-TASK-004-worker
=======
>>>>>>> noctifab/task-US-001-TASK-003-worker
=======
>>>>>>> noctifab/task-US-001-TASK-001-worker
import unittest

from src.store import Store


class TestStore(unittest.TestCase):
    def setUp(self) -> None:
        self.current_time = 1000.0
        self.store = Store(clock=lambda: self.current_time)

    def test_set_and_get_round_trip(self) -> None:
        self.assertTrue(self.store.set("k1", "v1"))
        self.assertEqual(self.store.get("k1"), "v1")
        self.assertIsNone(self.store.get("missing"))

    def test_set_replaces_value_and_removes_previous_expiration(self) -> None:
        self.store.set("k1", "old", expire_at=1010.0)
        self.assertTrue(self.store.set("k1", "new"))

        self.current_time = 1020.0
        self.assertEqual(self.store.get("k1"), "new")

    def test_conditional_set_nx_and_xx(self) -> None:
        self.assertTrue(self.store.set("new", "value", nx=True))
        self.assertFalse(self.store.set("new", "other", nx=True))
        self.assertEqual(self.store.get("new"), "value")

        self.assertFalse(self.store.set("missing", "value", xx=True))
        self.assertTrue(self.store.set("new", "updated", xx=True))
        self.assertEqual(self.store.get("new"), "updated")

    def test_delete_and_exists_for_multiple_keys(self) -> None:
        self.store.set("one", "1")
        self.store.set("two", "2")

        self.assertEqual(self.store.exists("one", "two", "missing"), 2)
        self.assertEqual(self.store.delete("one", "missing", "one", "two"), 2)
        self.assertEqual(self.store.exists("one", "two"), 0)
        self.assertEqual(self.store.delete("one", "two"), 0)

    def test_expiration_is_lazy_and_boundary_is_inclusive(self) -> None:
        self.store.set("k1", "v1", expire_at=1005.0)
        self.current_time = 1004.999
        self.assertEqual(self.store.get("k1"), "v1")
        self.assertEqual(self.store.exists("k1"), 1)

        self.current_time = 1005.0
        self.assertIsNone(self.store.get("k1"))
        self.assertEqual(self.store.exists("k1"), 0)
        self.assertEqual(self.store.delete("k1"), 0)

    def test_expired_key_is_not_returned_by_keys(self) -> None:
        self.store.set("alive", "1")
        self.store.set("temporary", "2", expire_at=1005.0)
        self.current_time = 1005.0

        self.assertEqual(self.store.keys("*"), ["alive"])
        self.assertEqual(self.store.keys("temp*"), [])

    def test_expire_and_ttl_use_injected_clock(self) -> None:
        self.store.set("k1", "v1")
        self.assertEqual(self.store.ttl("k1"), -1)
        self.assertTrue(self.store.expire("k1", 5.0))
        self.assertEqual(self.store.ttl("k1"), 5)

        self.current_time = 1002.5
        self.assertEqual(self.store.ttl("k1"), 2)
        self.assertTrue(self.store.expire("k1", 0))
        self.assertIsNone(self.store.get("k1"))
        self.assertEqual(self.store.ttl("k1"), -2)
        self.assertFalse(self.store.expire("missing", 10))

    def test_incr_by_creates_and_updates_integer_values(self) -> None:
        self.assertEqual(self.store.incr_by("counter", 1), 1)
        self.assertEqual(self.store.incr_by("counter", 5), 6)
        self.assertEqual(self.store.incr_by("counter", -2), 4)
        self.assertEqual(self.store.get("counter"), "4")

    def test_incr_by_rejects_non_integer_value(self) -> None:
        self.store.set("counter", "not-an-integer")
        with self.assertRaisesRegex(ValueError, "not an integer"):
            self.store.incr_by("counter", 1)

    def test_flushall_removes_values_and_expiration(self) -> None:
        self.store.set("k1", "v1", expire_at=1001.0)
        self.store.set("k2", "v2")
        self.store.flushall()

        self.current_time = 2000.0
        self.assertEqual(self.store.keys("*"), [])
        self.assertEqual(self.store.exists("k1", "k2"), 0)
        self.assertIsNone(self.store.get("k1"))

    def test_lock_is_exposed_as_asyncio_lock(self) -> None:
        self.assertIsInstance(self.store.lock, asyncio.Lock)
        self.assertIs(self.store.lock, self.store.lock)





if __name__ == "__main__":
    unittest.main()
