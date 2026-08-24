import unittest

from src.resp import (
    Error,
    RESPError,
    RESPIncompleteError,
    SimpleString,
    decode_resp,
    encode_array,
    encode_bulk_string,
    encode_error,
    encode_resp,
    encode_simple_string,
    parse_command,
)


class TestRESPEncoding(unittest.TestCase):
    def test_encode_simple_string(self) -> None:
        self.assertEqual(encode_simple_string("OK"), b"+OK\r\n")
        self.assertEqual(encode_resp(SimpleString("OK")), b"+OK\r\n")

    def test_encode_error(self) -> None:
        self.assertEqual(encode_error("ERR unknown"), b"-ERR unknown\r\n")
        self.assertEqual(encode_resp(Error("ERR unknown")), b"-ERR unknown\r\n")

    def test_encode_bulk_string(self) -> None:
        self.assertEqual(encode_bulk_string("hello"), b"$5\r\nhello\r\n")
        self.assertEqual(encode_bulk_string(b"world"), b"$5\r\nworld\r\n")
        self.assertEqual(encode_bulk_string(None), b"$-1\r\n")
        self.assertEqual(encode_resp("hello"), b"$5\r\nhello\r\n")
        self.assertEqual(encode_resp(None), b"$-1\r\n")

    def test_encode_array(self) -> None:
        arr = ["PING", SimpleString("OK"), 100]
        expected = b"*3\r\n$4\r\nPING\r\n+OK\r\n:100\r\n"
        self.assertEqual(encode_array(arr), expected)
        self.assertEqual(encode_resp(arr), expected)
        self.assertEqual(encode_array(None), b"*-1\r\n")


class TestRESPDecoding(unittest.TestCase):
    def test_decode_simple_string(self) -> None:
        val, read = decode_resp(b"+OK\r\n")
        self.assertEqual(val, SimpleString("OK"))
        self.assertEqual(read, 5)

    def test_decode_error(self) -> None:
        val, read = decode_resp(b"-ERR wrong type\r\n")
        self.assertEqual(val, Error("ERR wrong type"))
        self.assertEqual(read, 17)

    def test_decode_integer(self) -> None:
        val, read = decode_resp(b":1000\r\n")
        self.assertEqual(val, 1000)
        self.assertEqual(read, 7)

    def test_decode_bulk_string(self) -> None:
        val, read = decode_resp(b"$5\r\nhello\r\n")
        self.assertEqual(val, b"hello")
        self.assertEqual(read, 11)

        # Null bulk string
        val_null, read_null = decode_resp(b"$-1\r\n")
        self.assertIsNone(val_null)
        self.assertEqual(read_null, 5)

    def test_decode_array(self) -> None:
        data = b"*2\r\n$4\r\nECHO\r\n$5\r\nhello\r\n"
        val, read = decode_resp(data)
        self.assertEqual(val, [b"ECHO", b"hello"])
        self.assertEqual(read, len(data))

        # Null array
        val_null, read_null = decode_resp(b"*-1\r\n")
        self.assertIsNone(val_null)
        self.assertEqual(read_null, 5)

    def test_partial_inputs(self) -> None:
        # Partial bulk string length
        with self.assertRaises(RESPIncompleteError):
            decode_resp(b"$5\r\nhel")

        # Partial simple string
        with self.assertRaises(RESPIncompleteError):
            decode_resp(b"+OK")

        # Partial array
        with self.assertRaises(RESPIncompleteError):
            decode_resp(b"*2\r\n$4\r\nECHO\r\n")

    def test_malformed_inputs(self) -> None:
        # Invalid prefix
        with self.assertRaises(RESPError):
            decode_resp(b"?hello\r\n")

        # Invalid bulk string length
        with self.assertRaises(RESPError):
            decode_resp(b"$abc\r\n")

        # Bulk string missing trailing CRLF
        with self.assertRaises(RESPError):
            decode_resp(b"$5\r\nhelloXX")


class TestParseCommand(unittest.TestCase):
    def test_parse_resp_command(self) -> None:
        buf = b"*2\r\n$4\r\nPING\r\n$4\r\nPONG\r\nrest"
        args, rem = parse_command(buf)
        self.assertEqual(args, [b"PING", b"PONG"])
        self.assertEqual(rem, b"rest")

    def test_parse_inline_command(self) -> None:
        buf = b"PING arg1 arg2\r\nrest"
        args, rem = parse_command(buf)
        self.assertEqual(args, [b"PING", b"arg1", b"arg2"])
        self.assertEqual(rem, b"rest")

    def test_parse_incomplete_command(self) -> None:
        buf = b"*2\r\n$4\r\nPING\r\n"
        args, rem = parse_command(buf)
        self.assertIsNone(args)
        self.assertEqual(rem, buf)


if __name__ == "__main__":
    unittest.main()
