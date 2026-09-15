import unittest
from src.resp import Decoder, encode

class RespTest(unittest.TestCase):
    def test_split_bulk_and_array(self) -> None:
        decoder = Decoder(); self.assertEqual(decoder.feed(b"*1\r\n$3\r\nfo"), [])
        self.assertEqual(decoder.feed(b"o\r\n"), [[b"foo"]])
        self.assertEqual(encode([b"x", 1]), b"*2\r\n$1\r\nx\r\n:1\r\n")
