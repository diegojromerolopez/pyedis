import unittest
from src.resp import Decoder, bulk, integer, simple

class RespTests(unittest.TestCase):
    def test_encoding(self) -> None:
        self.assertEqual(simple("OK"), b"+OK\r\n")
        self.assertEqual(integer(2), b":2\r\n")
        self.assertEqual(bulk("hello"), b"$5\r\nhello\r\n")

    def test_fragmented_and_pipelined(self) -> None:
        decoder = Decoder()
        self.assertEqual(decoder.feed(b"*2\r\n$3\r\nGE"), [])
        self.assertEqual(decoder.feed(b"T\r\n$1\r\nx\r\n*1\r\n$4\r\nPING\r\n"), [[b"GET", b"x"], [b"PING"]])

    def test_inline(self) -> None:
        self.assertEqual(Decoder().feed(b"PING hello\r\n"), [[b"PING", b"hello"]])

if __name__ == "__main__":
    unittest.main()
