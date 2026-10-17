import unittest

from src.handlers.hll.hll_codec import decode
from src.handlers.hll.pfadd import pfadd
from src.handlers.hll.pfcount import pfcount
from src.handlers.hll.pfmerge import pfmerge
from src.store import Store


class TestPFMerge(unittest.TestCase):
    def test_merge_writes_destination_and_supports_missing_sources(self) -> None:
        store = Store()
        pfadd(store, "one", [b"one"])
        pfadd(store, "two", [b"two"])
        pfmerge(store, "merged", ["one", "two", "missing"])
        self.assertEqual(pfcount(store, ["merged"]), 2)
        self.assertEqual(len(decode(store.get("merged").encode("latin1"))), 16384)

    def test_merge_with_no_sources_creates_empty_hll(self) -> None:
        store = Store()
        pfmerge(store, "empty", [])
        self.assertEqual(pfcount(store, ["empty"]), 0)


if __name__ == "__main__":
    unittest.main()
