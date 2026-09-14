import unittest
from src.resp import (
    RESPDecoder,
    encode_array,
    encode_bulk_string,
    encode_error,
    encode_integer,
    encode_simple_string,
)


class TestRESP(unittest.TestCase):
    def test_encoders(self) -> None:
        self.assertEqual(encode_simple_string("OK"), b"+OK\r\n")
        self.assertEqual(encode_error("ERR", "unknown"), b"-ERR unknown\r\n")
        self.assertEqual(encode_integer(42), b":42\r\n")
        self.assertEqual(encode_bulk_string("hello"), b"$5\r\nhello\r\n")
        self.assertEqual(encode_bulk_string(None), b"$-1\r\n")
        self.assertEqual(encode_array([b"foo", b"bar"]), b"*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n")
        self.assertEqual(encode_array([]), b"*0\r\n")

    def test_decoder_chunking_and_pipelining(self) -> None:
        decoder = RESPDecoder()
        decoder.feed(b"*2\r\n$3\r\nGE")
        self.assertEqual(decoder.decode_multi(), [])
        decoder.feed(b"T\r\n$3\r\nkey\r\n*1\r\n$4\r\nPING\r\n")
        cmds = decoder.decode_multi()
        self.assertEqual(cmds, [[b"GET", b"key"], [b"PING"]])

    def test_inline_command(self) -> None:
        decoder = RESPDecoder()
        decoder.feed(b"PING hello\r\n")
        cmds = decoder.decode_multi()
        self.assertEqual(cmds, [[b"PING", b"hello"]])


if __name__ == "__main__":
    unittest.main()
