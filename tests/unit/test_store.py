"""Unit tests for the in-memory store."""

import asyncio
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

    def test_incr_by_supports_negative_delta_and_missing_key_defaults_to_zero(self) -> None:
        self.assertEqual(self.store.incr_by("fresh", -5), -5)
        self.assertEqual(self.store.get("fresh"), "-5")

    def test_set_without_expire_at_clears_previous_ttl(self) -> None:
        self.store.set("key", "first", expire_at=1005.0)
        self.assertEqual(self.store.ttl("key"), 5)
        self.store.set("key", "second")
        self.assertEqual(self.store.ttl("key"), -1)
        self.clock.value = 2000.0
        self.assertEqual(self.store.get("key"), "second")

    def test_keys_actively_sweeps_expired_entries_without_being_queried(self) -> None:
        self.store.set("alive", "a")
        self.store.set("dying", "b", expire_at=1005.0)
        self.clock.value = 1005.0
        result = self.store.keys("*")
        self.assertEqual(result, ["alive"])
        # The active sweep must have purged internal state, not merely filtered output.
        self.assertNotIn("dying", self.store._strings)
        self.assertNotIn("dying", self.store._expires)

    def test_delete_counts_only_existing_keys_among_mixed_arguments(self) -> None:
        self.store.set("k1", "v1")
        self.store.set("k2", "v2")
        self.assertEqual(self.store.delete("k1", "missing", "k2"), 2)
        self.assertEqual(self.store.exists("k1", "k2"), 0)

    def test_exists_counts_repeated_and_expired_keys_correctly(self) -> None:
        self.store.set("k1", "v1")
        self.store.set("k2", "v2", expire_at=1005.0)
        self.clock.value = 1005.0
        self.assertEqual(self.store.exists("k1", "k1", "k2"), 2)


class TestStoreLock(unittest.IsolatedAsyncioTestCase):
    async def test_injected_lock_enforces_mutual_exclusion_across_coroutines(self) -> None:
        store = Store(clock=MutableClock(0.0))
        events: list[str] = []

        async def critical_section(name: str) -> None:
            async with store.lock:
                events.append(f"{name}-start")
                await asyncio.sleep(0.01)
                events.append(f"{name}-end")

        await asyncio.gather(critical_section("a"), critical_section("b"))

        # Mutual exclusion means one coroutine's start/end must not interleave with the other's.
        self.assertIn(events[:2], (["a-start", "a-end"], ["b-start", "b-end"]))
        self.assertEqual(len(events), 4)

    async def test_lock_is_shared_asyncio_lock_instance(self) -> None:
        store = Store(clock=MutableClock(0.0))
        self.assertIsInstance(store.lock, asyncio.Lock)
        self.assertIs(store.lock, store.lock)


if __name__ == "__main__":
    unittest.main()
