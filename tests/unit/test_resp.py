import unittest
from src.resp import Decoder, encode

class RespTest(unittest.TestCase):
    def test_incremental(self) -> None:
        decoder = Decoder(); self.assertEqual(decoder.feed(b'*1\r\n$4\r\nPING'), [])
        frame = decoder.feed(b'\r\n')[0]
        self.assertEqual(frame.value[0].value, b'PING')
        self.assertEqual(encode(b'ok'), b'$2\r\nok\r\n')
