import unittest

from src.handlers.hll.pfadd import pfadd
from src.handlers.hll.pfcount import pfcount
from src.store import Store


class TestPFCount(unittest.TestCase):
    def test_empty_and_missing_keys_have_zero_cardinality(self) -> None:
        store = Store()
        self.assertEqual(pfcount(store, []), 0)
        self.assertEqual(pfcount(store, ["missing"]), 0)

    def test_estimate_is_within_one_percent_for_ten_thousand_values(self) -> None:
        store = Store()
        pfadd(store, "large", [f"value-{i}".encode() for i in range(10000)])
        estimate = pfcount(store, ["large"])
        self.assertLessEqual(abs(estimate - 10000), 100)

    def test_count_merges_registers_without_mutating_sources(self) -> None:
        store = Store()
        pfadd(store, "left", [b"a", b"b"])
        pfadd(store, "right", [b"c", b"d"])
        left = store.get("left")
        right = store.get("right")
        self.assertEqual(pfcount(store, ["left", "right"]), 4)
        self.assertEqual(store.get("left"), left)
        self.assertEqual(store.get("right"), right)


if __name__ == "__main__":
    unittest.main()
