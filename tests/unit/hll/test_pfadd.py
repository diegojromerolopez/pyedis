import unittest

from src.handlers.hll.hll_codec import REGISTERS, decode, encode
from src.handlers.hll.pfadd import pfadd
from src.store import Store


class TestPFAdd(unittest.TestCase):
    def test_add_mutates_registers_and_returns_zero_for_duplicates(self) -> None:
        store = Store()
        self.assertEqual(pfadd(store, "hll", [b"one", b"two", b"three"]), 1)
        payload = store.get("hll")
        self.assertIsNotNone(payload)
        registers = decode(payload.encode("latin1"))
        self.assertEqual(len(registers), REGISTERS)
        self.assertGreater(sum(registers), 0)
        self.assertEqual(pfadd(store, "hll", [b"one", b"two", b"three"]), 0)
        self.assertEqual(store.get("hll"), payload)

    def test_codec_is_dense_and_rejects_invalid_payloads(self) -> None:
        payload = encode(bytearray(REGISTERS))
        self.assertEqual(len(payload), REGISTERS + 4)
        self.assertEqual(decode(payload), bytearray(REGISTERS))
        with self.assertRaises(ValueError):
            decode(b"bad")
        with self.assertRaises(ValueError):
            encode(bytes([64]) + bytes(REGISTERS - 1))


if __name__ == "__main__":
    unittest.main()
