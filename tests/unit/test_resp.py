"""Unit tests for RESP framing and streaming decoding."""

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
    def test_scalar_encoders(self) -> None:
        self.assertEqual(encode_simple_string("OK"), b"+OK\r\n")
        self.assertEqual(encode_error("syntax error"), b"-ERR syntax error\r\n")
        self.assertEqual(encode_error("bad", "WRONGTYPE"), b"-WRONGTYPE bad\r\n")
        self.assertEqual(encode_integer(42), b":42\r\n")

    def test_bulk_strings_support_text_bytes_and_null(self) -> None:
        self.assertEqual(encode_bulk_string("hé"), "$3\r\nhé\r\n".encode())
        self.assertEqual(encode_bulk_string(b"hello"), b"$5\r\nhello\r\n")
        self.assertEqual(encode_bulk_string(None), b"$-1\r\n")

    def test_arrays_and_nested_resp_values(self) -> None:
        self.assertEqual(encode_array(["PING"]), b"*1\r\n$4\r\nPING\r\n")
        self.assertEqual(
            encode_resp(["SET", "key", 7, None]),
            b"*4\r\n$3\r\nSET\r\n$3\r\nkey\r\n:7\r\n$-1\r\n",
        )
        self.assertEqual(encode_array(None), b"*-1\r\n")


class TestRESPDecoding(unittest.TestCase):
    def test_decode_multi_bulk_and_multiple_commands(self) -> None:
        raw = bytearray(b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\nPING\r\n")
        commands, remainder = decode_resp_stream(raw)
        self.assertEqual(commands, [[b"GET", b"key"], [b"PING"]])
        self.assertEqual(remainder, b"")

    def test_decode_inline_command(self) -> None:
        commands, remainder = decode_resp_stream(bytearray(b"PING hello\r\n"))
        self.assertEqual(commands, [[b"PING", b"hello"]])
        self.assertEqual(remainder, b"")

    def test_incomplete_frame_is_returned_as_remainder(self) -> None:
        raw = bytearray(b"*2\r\n$3\r\nGET\r\n$3\r\nke")
        commands, remainder = decode_resp_stream(raw)
        self.assertEqual(commands, [])
        self.assertEqual(remainder, bytes(raw))

    def test_decoder_does_not_mutate_input_buffer(self) -> None:
        raw = bytearray(b"PING\r\n")
        original = bytes(raw)
        decode_resp_stream(raw)
        self.assertEqual(bytes(raw), original)

    def test_fragmented_resp_frame_is_decoded_only_when_complete(self) -> None:
        frame = b"*2\r\n$3\r\nGET\r\n$5\r\nhello\r\n"
        remainder = bytearray()
        decoded: list[list[bytes]] = []

        for byte in frame:
            remainder.extend([byte])
            commands, remainder = decode_resp_stream(remainder)
            decoded.extend(commands)

        self.assertEqual(decoded, [[b"GET", b"hello"]])
        self.assertEqual(remainder, bytearray())

    def test_pipelined_frames_survive_fragmented_reads(self) -> None:
        payload = b"*1\r\n$4\r\nPING\r\n*2\r\n$4\r\nECHO\r\n$5\r\nhello\r\nSET key value\r\n"
        remainder = bytearray()
        decoded: list[list[bytes]] = []

        for start in range(0, len(payload), 3):
            remainder.extend(payload[start : start + 3])
            commands, remainder = decode_resp_stream(remainder)
            decoded.extend(commands)

        self.assertEqual(
            decoded,
            [[b"PING"], [b"ECHO", b"hello"], [b"SET", b"key", b"value"]],
        )
        self.assertEqual(remainder, bytearray())

    def test_incomplete_array_header_and_bulk_header_are_retained(self) -> None:
        for raw in (b"*", b"*2\r", b"*1\r\n$", b"*1\r\n$4\r\nPI"):
            with self.subTest(raw=raw):
                commands, remainder = decode_resp_stream(bytearray(raw))
                self.assertEqual(commands, [])
                self.assertEqual(remainder, raw)

    def test_bulk_framing_uses_utf8_byte_length_and_preserves_binary_data(self) -> None:
        value = "€"
        encoded = encode_resp(value)
        self.assertEqual(encoded, b"$3\r\n\xe2\x82\xac\r\n")

        commands, remainder = decode_resp_stream(bytearray(b"*1\r\n$4\r\nDATA\r\n"))
        self.assertEqual(commands, [[b"DATA"]])
        self.assertEqual(remainder, bytearray())


if __name__ == "__main__":
    unittest.main()
