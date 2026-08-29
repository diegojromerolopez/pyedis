import asyncio
import unittest
from src.resp import (
    encode_simple_string,
    encode_error,
    encode_integer,
    encode_bulk_string,
    encode_array,
    parse_resp_command,
)


class TestRespEncoding(unittest.TestCase):
    def test_encode_simple_string(self):
        self.assertEqual(encode_simple_string("OK"), b"+OK\r\n")
        self.assertEqual(encode_simple_string("PONG"), b"+PONG\r\n")

    def test_encode_error(self):
        self.assertEqual(encode_error("ERR test"), b"-ERR test\r\n")

    def test_encode_integer(self):
        self.assertEqual(encode_integer(100), b":100\r\n")
        self.assertEqual(encode_integer(-1), b":-1\r\n")

    def test_encode_bulk_string(self):
        self.assertEqual(encode_bulk_string("hello"), b"$5\r\nhello\r\n")
        self.assertEqual(encode_bulk_string(b"raw"), b"$3\r\nraw\r\n")
        self.assertEqual(encode_bulk_string(None), b"$-1\r\n")

    def test_encode_array(self):
        self.assertEqual(encode_array(["PING"]), b"*1\r\n$4\r\nPING\r\n")
        self.assertEqual(encode_array(None), b"*-1\r\n")


class TestRespParsing(unittest.TestCase):
    def test_parse_inline(self):
        async def run():
            reader = asyncio.StreamReader()
            reader.feed_data(b"PING\r\n")
            reader.feed_eof()
            cmd = await parse_resp_command(reader)
            self.assertEqual(cmd, ["PING"])

        asyncio.run(run())

    def test_parse_array(self):
        async def run():
            reader = asyncio.StreamReader()
            reader.feed_data(b"*2\r\n$4\r\nECHO\r\n$5\r\nhello\r\n")
            reader.feed_eof()
            cmd = await parse_resp_command(reader)
            self.assertEqual(cmd, ["ECHO", "hello"])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
