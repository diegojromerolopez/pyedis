"""Characterization tests for RESP serialization and stream decoding."""

import unittest

from src.resp import (
    decode_resp_stream,
    encode_array,
    encode_bulk_string,
    encode_error,
    encode_integer,
    encode_resp,
    encode_simple_string,
)


class TestRESPEncoding(unittest.TestCase):
    def test_simple_strings_include_delimiter(self) -> None:
        self.assertEqual(encode_simple_string("OK"), b"+OK\r\n")
        self.assertEqual(encode_simple_string("hé"), "+hé\r\n".encode())

    def test_errors_and_integers(self) -> None:
        self.assertEqual(encode_error("bad"), b"-ERR bad\r\n")
        self.assertEqual(encode_error("bad", "WRONGTYPE"), b"-WRONGTYPE bad\r\n")
        self.assertEqual(encode_integer(-7), b":-7\r\n")

    def test_bulk_strings_and_arrays(self) -> None:
        self.assertEqual(encode_bulk_string("hello"), b"$5\r\nhello\r\n")
        self.assertEqual(encode_bulk_string(None), b"$-1\r\n")
        self.assertEqual(encode_array(["a", 2]), b"*2\r\n$1\r\na\r\n:2\r\n")
        self.assertEqual(encode_resp(True), b":1\r\n")

    def test_fragmented_and_pipelined_commands(self) -> None:
        first = bytearray(b"*1\r\n$4\r\nPING\r\n*2\r\n$3\r\nGET\r\n$3\r\nke")
        commands, remainder = decode_resp_stream(first)
        self.assertEqual(commands, [[b"PING"]])
        remainder.extend(b"y\r\n")
        commands, remainder = decode_resp_stream(remainder)
        self.assertEqual(commands, [[b"GET", b"key"]])
        self.assertEqual(remainder, bytearray())

    def test_inline_commands_ignore_blank_lines(self) -> None:
        commands, remainder = decode_resp_stream(bytearray(b"\r\nPING\r\nGET key\r\n"))
        self.assertEqual(commands, [[b"PING"], [b"GET", b"key"]])
        self.assertEqual(remainder, bytearray())


if __name__ == "__main__":
    unittest.main()
