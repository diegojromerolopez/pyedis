import unittest
from src.resp import Decoder, bulk, integer, simple

class RespTests(unittest.TestCase):
    def test_encoding(self) -> None:
        self.assertEqual(simple('OK'), b'+OK\r\n')
        self.assertEqual(integer(4), b':4\r\n')
        self.assertEqual(bulk('hello'), b'$5\r\nhello\r\n')
    def test_chunks_and_pipeline(self) -> None:
        d = Decoder(); self.assertEqual(d.feed(b'*1\r\n$4\r\n'), [])
        self.assertEqual(d.feed(b'PING\r\n*1\r\n$4\r\nPING\r\n'), [[b'PING'], [b'PING']])
    def test_inline(self) -> None:
        self.assertEqual(Decoder().feed(b'PING hello\r\n'), [[b'PING', b'hello']])
