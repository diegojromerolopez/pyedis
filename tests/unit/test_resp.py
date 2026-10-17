"""RESP serialization tests."""
import unittest
from src.resp import decode_resp_stream, encode_array, encode_bulk_string, encode_error, encode_integer, encode_simple_string

class TestRESPEncoding(unittest.TestCase):
    def test_simple_string(self) -> None:
        self.assertEqual(encode_simple_string("OK"), b"+OK\r\n")

    def test_error(self) -> None:
        self.assertEqual(encode_error("syntax error"), b"-ERR syntax error\r\n")

    def test_integer(self) -> None:
        self.assertEqual(encode_integer(42), b":42\r\n")

    def test_bulk_string(self) -> None:
        self.assertEqual(encode_bulk_string("hello"), b"$5\r\nhello\r\n")
        self.assertEqual(encode_bulk_string(None), b"$-1\r\n")

    def test_decode_stream(self) -> None:
        buf = bytearray(b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n")
        cmds, rem = decode_resp_stream(buf)
        self.assertEqual(len(cmds), 1)
        self.assertEqual(cmds[0], [b"GET", b"key"])
        self.assertEqual(rem, b"")

if __name__ == "__main__":
    unittest.main()
