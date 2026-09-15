import unittest
from src.resp import Decoder, encode


class RespTests(unittest.TestCase):
    def test_chunked_bulk(self) -> None:
        decoder = Decoder()
        self.assertEqual(decoder.feed(b"*1\r\n$3\r\n"), [])
        self.assertEqual(decoder.feed(b"abc\r\n"), [[b"abc"]])

    def test_encoding(self) -> None:
        self.assertEqual(encode(["a", 2]), b"*2\r\n$1\r\na\r\n:2\r\n")
