import unittest
from src.resp import encode_resp, encode_simple_string, encode_error, RESPParser


class TestRESP(unittest.TestCase):
    def test_encoding(self) -> None:
        self.assertEqual(encode_simple_string("OK"), b"+OK\r\n")
        self.assertEqual(encode_error("err"), b"-ERR err\r\n")
        self.assertEqual(encode_resp(10), b":10\r\n")
        self.assertEqual(encode_resp("hi"), b"$2\r\nhi\r\n")
        self.assertEqual(encode_resp(None), b"$-1\r\n")

    def test_parser_pipelined(self) -> None:
        parser = RESPParser()
        parser.feed(b"*1\r\n$4\r\nPING\r\n*1\r\n$4\r\nPING\r\n")
        res1 = parser.parse_one()
        res2 = parser.parse_one()
        self.assertEqual(res1, [b"PING"])
        self.assertEqual(res2, [b"PING"])


if __name__ == "__main__":
    unittest.main()
