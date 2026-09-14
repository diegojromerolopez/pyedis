import unittest
from src.resp import Decoder, array, bulk, error, integer, simple


class RespTests(unittest.TestCase):
    def test_encoding(self) -> None:
        self.assertEqual(simple("OK"), b"+OK\r\n")
        self.assertEqual(error("ERR bad"), b"-ERR bad\r\n")
        self.assertEqual(integer(3), b":3\r\n")
        self.assertEqual(bulk("hello"), b"$5\r\nhello\r\n")
        self.assertEqual(bulk(None), b"$-1\r\n")
        self.assertEqual(array([bulk("a"), bulk("b")]), b"*2\r\n$1\r\na\r\n$1\r\nb\r\n")

    def test_stream_and_pipeline(self) -> None:
        decoder = Decoder()
        self.assertEqual(decoder.feed(b"*1\r\n$4\r\nP"), [])
        self.assertEqual(decoder.feed(b"ING\r\nPING\r\n"), [[b"PING"], [b"PING"]])

    def test_inline(self) -> None:
        self.assertEqual(Decoder().feed(b"SET k value\r\n"), [[b"SET", b"k", b"value"]])
