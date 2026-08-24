import unittest
from src.resp import (
    Error,
    SimpleString,
    decode_resp,
    encode_array,
    encode_bulk_string,
    encode_error,
    encode_integer,
    encode_resp,
    encode_simple_string,
    parse_command,
)


class TestRESP(unittest.TestCase):
    def test_encode_integer(self) -> None:
        self.assertEqual(encode_integer(100), b":100\r\n")
        self.assertEqual(encode_integer(-42), b":-42\r\n")
        self.assertEqual(encode_resp(42), b":42\r\n")

    def test_encode_null_bulk_string(self) -> None:
        self.assertEqual(encode_bulk_string(None), b"$-1\r\n")
        self.assertEqual(encode_resp(None), b"$-1\r\n")

    def test_encode_simple_string(self) -> None:
        self.assertEqual(encode_simple_string("OK"), b"+OK\r\n")
        self.assertEqual(encode_resp(SimpleString("OK")), b"+OK\r\n")

    def test_encode_error(self) -> None:
        self.assertEqual(encode_error("ERR test"), b"-ERR test\r\n")
        self.assertEqual(encode_resp(Error("ERR test")), b"-ERR test\r\n")

    def test_encode_bulk_string(self) -> None:
        self.assertEqual(encode_bulk_string("hello"), b"$5\r\nhello\r\n")

    def test_encode_array(self) -> None:
        self.assertEqual(
            encode_array(["foo", "bar"]), b"*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
        )
        self.assertEqual(encode_array(None), b"*-1\r\n")

    def test_decode_resp_integer(self) -> None:
        val, consumed = decode_resp(b":1000\r\n")
        self.assertEqual(val, 1000)
        self.assertEqual(consumed, 7)

    def test_decode_resp_null_bulk_string(self) -> None:
        val, consumed = decode_resp(b"$-1\r\n")
        self.assertIsNone(val)
        self.assertEqual(consumed, 5)

    def test_parse_command(self) -> None:
        cmd, rem = parse_command(b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n")
        self.assertEqual(cmd, [b"GET", b"key"])
        self.assertEqual(rem, b"")


if __name__ == "__main__":
    unittest.main()
