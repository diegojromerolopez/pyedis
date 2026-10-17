"""RESP serialization tests."""

import unittest
from src.resp import (
    decode_resp_stream,
    encode_array,
    encode_bulk_string,
    encode_error,
    encode_integer,
    encode_simple_string,
)


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

    def test_array(self) -> None:
        self.assertEqual(
            encode_array(["SET", "key", "value"]),
            b"*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n",
        )
        self.assertEqual(encode_array([]), b"*0\r\n")

    def test_decode_stream(self) -> None:
        buf = bytearray(b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n")
        cmds, rem = decode_resp_stream(buf)
        self.assertEqual(len(cmds), 1)
        self.assertEqual(cmds[0], [b"GET", b"key"])
        self.assertEqual(rem, b"")

    def test_array_encoding(self) -> None:
        self.assertEqual(
            encode_array(["GET", "key"]),
            b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n",
        )
        self.assertEqual(encode_array(None), b"*-1\r\n")

    def test_decode_fragmented_and_pipelined_frames(self) -> None:
        first, remainder = decode_resp_stream(bytearray(b"*1\r\n$4\r\nPI"))
        self.assertEqual(first, [])
        self.assertEqual(remainder, b"*1\r\n$4\r\nPI")

        payload = remainder + b"NG\r\n*2\r\n$4\r\nECHO\r\n$2\r\nhi\r\n"
        commands, remainder = decode_resp_stream(bytearray(payload))
        self.assertEqual(commands, [[b"PING"], [b"ECHO", b"hi"]])
        self.assertEqual(remainder, b"")

    def test_decode_fragmented_frame(self) -> None:
        first = bytearray(b"*2\r\n$3\r\nGE")
        cmds, rem = decode_resp_stream(first)
        self.assertEqual(cmds, [])
        self.assertEqual(rem, first)

        rem.extend(b"T\r\n$3\r\nkey\r\n")
        cmds, rem = decode_resp_stream(rem)
        self.assertEqual(cmds, [[b"GET", b"key"]])
        self.assertEqual(rem, b"")

    def test_decode_pipelined_frames(self) -> None:
        buf = bytearray(b"*1\r\n$4\r\nPING\r\n*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n")
        cmds, rem = decode_resp_stream(buf)
        self.assertEqual(cmds, [[b"PING"], [b"GET", b"key"]])
        self.assertEqual(rem, b"")


if __name__ == "__main__":
    unittest.main()
