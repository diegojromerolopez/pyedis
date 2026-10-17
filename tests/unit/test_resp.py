"""Unit tests for RESP framing engine."""
import unittest
from src.resp import decode_resp_stream, encode_array, encode_bulk_string, encode_error, encode_integer, encode_simple_string

class TestRESPEncoding(unittest.TestCase):
    def test_encode_simple_string(self) -> None:
        self.assertEqual(encode_simple_string("OK"), b"+OK\r\n")

    def test_encode_error(self) -> None:
        self.assertEqual(encode_error("syntax error"), b"-ERR syntax error\r\n")

    def test_encode_integer(self) -> None:
        self.assertEqual(encode_integer(42), b":42\r\n")

    def test_encode_bulk_string(self) -> None:
        self.assertEqual(encode_bulk_string("hello"), b"$5\r\nhello\r\n")
        self.assertEqual(encode_bulk_string(None), b"$-1\r\n")

    def test_encode_array(self) -> None:
        self.assertEqual(encode_array(["PING"]), b"*1\r\n$4\r\nPING\r\n")

class TestRESPDecoding(unittest.TestCase):
    def test_decode_multi_bulk(self) -> None:
        raw = bytearray(b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n")
        cmds, rem = decode_resp_stream(raw)
        self.assertEqual(cmds, [[b"GET", b"key"]])
        self.assertEqual(rem, b"")

    def test_decode_inline(self) -> None:
        raw = bytearray(b"PING hello\r\n")
        cmds, rem = decode_resp_stream(raw)
        self.assertEqual(cmds, [[b"PING", b"hello"]])
        self.assertEqual(rem, b"")

if __name__ == "__main__":
    unittest.main()
