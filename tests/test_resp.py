import unittest
from src.resp import Decoder, array, bulk, error, integer, simple


class RESPTest(unittest.TestCase):
    def test_encoders(self) -> None:
        self.assertEqual(simple("OK"), b"+OK\r\n")
        self.assertEqual(error("ERR bad"), b"-ERR bad\r\n")
        self.assertEqual(integer(2), b":2\r\n")
        self.assertEqual(bulk("hi"), b"$2\r\nhi\r\n")
        self.assertEqual(array(["GET", "key"]), b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n")

    def test_fragmented_and_pipelined(self) -> None:
        decoder = Decoder()
        self.assertEqual(decoder.feed(b"*1\r\n$4\r\nPI"), [])
        self.assertEqual(decoder.feed(b"NG\r\n*1\r\n$4\r\nPING\r\n"), [[b"PING"], [b"PING"]])

    def test_inline(self) -> None:
        self.assertEqual(Decoder().feed(b"PING hello\r\n"), [[b"PING", b"hello"]])
