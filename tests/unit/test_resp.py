import unittest
from src.resp import Decoder, array, bulk, integer, simple


class RespTests(unittest.TestCase):
    def test_encoding(self) -> None:
        self.assertEqual(simple("OK"), b"+OK\r\n")
        self.assertEqual(integer(2), b":2\r\n")
        self.assertEqual(bulk("hello"), b"$5\r\nhello\r\n")
        self.assertEqual(array(["GET", "key"]), b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n")

    def test_chunking_and_pipeline(self) -> None:
        decoder = Decoder()
        self.assertEqual(decoder.feed(b"*2\r\n$3\r\n"), [])
        self.assertEqual(decoder.feed(b"GET\r\n$3\r\nkey\r\nPING\r\n"), [[b"GET", b"key"], [b"PING"]])

    def test_inline(self) -> None:
        self.assertEqual(Decoder().feed(b"SET k value\r\n"), [[b"SET", b"k", b"value"]])
