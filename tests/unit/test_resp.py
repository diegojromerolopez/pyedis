"""Characterization tests for RESP serialization and stream decoding."""
from pathlib import Path
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
    def test_simple_strings_include_resp_delimiter(self) -> None:
        self.assertEqual(encode_simple_string("OK"), b"+OK\r\n")
        self.assertEqual(encode_simple_string("PONG"), b"+PONG\r\n")
        self.assertEqual(encode_simple_string("hé"), " +hé\r\n".strip().encode("utf-8"))

    def test_errors_use_default_and_custom_error_types(self) -> None:
        self.assertEqual(encode_error("syntax error"), b"-ERR syntax error\r\n")
        self.assertEqual(encode_error("bad request", "WRONGTYPE"), b"-WRONGTYPE bad request\r\n")

    def test_integers_include_negative_and_zero_values(self) -> None:
        self.assertEqual(encode_integer(42), b":42\r\n")
        self.assertEqual(encode_integer(0), b":0\r\n")
        self.assertEqual(encode_integer(-7), b":-7\r\n")

    def test_bulk_strings_encode_bytes_by_byte_length(self) -> None:
        self.assertEqual(encode_bulk_string("hello"), b"$5\r\nhello\r\n")
        self.assertEqual(encode_bulk_string("hé"), b"$3\r\nhé\r\n")
        self.assertEqual(encode_bulk_string(b"\x00\xff"), b"$2\r\n\x00\xff\r\n")
        self.assertEqual(encode_bulk_string(None), b"$-1\r\n")

    def test_arrays_encode_each_value_recursively(self) -> None:
        self.assertEqual(
            encode_array(["GET", "key", 2]),
            b"*3\r\n$3\r\nGET\r\n$3\r\nkey\r\n:2\r\n",
        )
        self.assertEqual(
            encode_array([None, ["nested"], True, 1.5]),
            b"*4\r\n$-1\r\n*1\r\n$6\r\nnested\r\n:1\r\n$3\r\n1.5\r\n",
        )
        self.assertEqual(encode_array(None), b"*-1\r\n")
        self.assertEqual(encode_array([]), b"*0\r\n")

    def test_encode_resp_dispatches_supported_values(self) -> None:
        self.assertEqual(encode_resp(None), b"$-1\r\n")
        self.assertEqual(encode_resp(False), b":0\r\n")
        self.assertEqual(encode_resp(True), b":1\r\n")
        self.assertEqual(encode_resp(3.25), b"$4\r\n3.25\r\n")
        self.assertEqual(encode_resp(bytearray(b"abc")), b"$3\r\nabc\r\n")
        self.assertEqual(encode_resp(object()), b"-ERR unsupported payload type\r\n")

    def test_resp_source_stays_below_size_limit(self) -> None:
        source = Path(__file__).resolve().parents[2] / "src" / "resp.py"
        self.assertLess(len(source.read_text(encoding="utf-8").splitlines()), 500)


class TestRESPStreamDecoding(unittest.TestCase):
    def test_fragmented_array_frame_decodes_only_after_complete_frame(self) -> None:
        frame = b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n"
        pending = bytearray()
        commands: list[list[bytes]] = []

        for byte in frame:
            pending.extend(bytes((byte,)))
            decoded, pending = decode_resp_stream(pending)
            commands.extend(decoded)

        self.assertEqual(commands, [[b"GET", b"key"]])
        self.assertEqual(pending, bytearray())

    def test_fragmented_frame_can_be_resumed_using_returned_remainder(self) -> None:
        first = bytearray(b"*2\r\n$3\r\nGET\r\n$3\r\nke")
        commands, remainder = decode_resp_stream(first)
        self.assertEqual(commands, [])
        self.assertEqual(remainder, first)

        remainder.extend(b"y\r\n")
        commands, remainder = decode_resp_stream(remainder)
        self.assertEqual(commands, [[b"GET", b"key"]])
        self.assertEqual(remainder, bytearray())

    def test_pipelined_array_commands_are_decoded_in_order(self) -> None:
        pipeline = (
            b"*2\r\n$4\r\nPING\r\n$4\r\nname\r\n"
            b"*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n"
        )
        commands, remainder = decode_resp_stream(bytearray(pipeline))
        self.assertEqual(
            commands,
            [[b"PING", b"name"], [b"SET", b"key", b"value"]],
        )
        self.assertEqual(remainder, bytearray())

    def test_complete_command_and_partial_pipelined_command_preserve_tail(self) -> None:
        data = bytearray(b"*1\r\n$4\r\nPING\r\n*2\r\n$3\r\nGET\r\n$3\r\nke")
        commands, remainder = decode_resp_stream(data)
        self.assertEqual(commands, [[b"PING"]])
        self.assertEqual(remainder, bytearray(b"*2\r\n$3\r\nGET\r\n$3\r\nke"))

        remainder.extend(b"y\r\n")
        commands, remainder = decode_resp_stream(remainder)
        self.assertEqual(commands, [[b"GET", b"key"]])
        self.assertEqual(remainder, bytearray())

    def test_inline_lines_are_decoded_and_blank_lines_are_ignored(self) -> None:
        commands, remainder = decode_resp_stream(bytearray(b"\r\nPING\r\nGET key\r\n"))
        self.assertEqual(commands, [[b"PING"], [b"GET", b"key"]])
        self.assertEqual(remainder, bytearray())


if __name__ == "__main__":
    unittest.main()
