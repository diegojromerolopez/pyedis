import unittest

from src.handlers.bitmaps.bitop import bitop
from src.store import Store


class TestBitop(unittest.TestCase):
    def test_and_or_xor_and_not_preserve_raw_bytes(self) -> None:
        store = Store()
        store.set("a", bytes([0x00, 0xF0, 0xFF]).decode("latin1"))
        store.set("b", bytes([0xFF, 0x0F]).decode("latin1"))

        self.assertEqual(bitop(store, "AND", "and", ["a", "b"]), 3)
        self.assertEqual(store.get("and").encode("latin1"), bytes([0x00, 0x00, 0x00]))
        self.assertEqual(bitop(store, "OR", "or", ["a", "b"]), 3)
        self.assertEqual(store.get("or").encode("latin1"), bytes([0xFF, 0xFF, 0xFF]))
        self.assertEqual(bitop(store, "XOR", "xor", ["a", "b"]), 3)
        self.assertEqual(store.get("xor").encode("latin1"), bytes([0xFF, 0xFF, 0xFF]))
        self.assertEqual(bitop(store, "NOT", "not", ["a"]), 3)
        self.assertEqual(store.get("not").encode("latin1"), bytes([0xFF, 0x0F, 0x00]))

    def test_missing_sources_are_zero_and_result_uses_longest_source(self) -> None:
        store = Store()
        store.set("short", bytes([0xF0]).decode("latin1"))
        self.assertEqual(bitop(store, "OR", "result", ["short", "missing"]), 1)
        self.assertEqual(store.get("result").encode("latin1"), bytes([0xF0]))
        self.assertEqual(bitop(store, "AND", "empty", ["missing"]), 0)
        self.assertEqual(store.get("empty"), "")

    def test_destination_mutation_clears_expiration(self) -> None:
        store = Store()
        store.set("source", "x")
        store.set("destination", "old")
        self.assertTrue(store.expire("destination", 100))
        bitop(store, "NOT", "destination", ["source"])
        self.assertEqual(store.ttl("destination"), -1)

    def test_invalid_operations_and_not_arity_are_rejected(self) -> None:
        store = Store()
        with self.assertRaises(ValueError):
            bitop(store, "NOT", "out", ["a", "b"])
        with self.assertRaises(ValueError):
            bitop(store, "AND", "out", [])
        with self.assertRaises(ValueError):
            bitop(store, "ROTATE", "out", ["a"])


if __name__ == "__main__":
    unittest.main()
