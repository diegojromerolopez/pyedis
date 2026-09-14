import asyncio
import tempfile
import unittest
from src.commands import Dispatcher
from src.persistence import AOF
from src.store import Store


class CommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.dispatcher = Dispatcher(Store(), AOF(self.directory.name + "/dump.aof", False))

    def tearDown(self) -> None:
        self.directory.cleanup()

    def run(self, *parts: bytes) -> bytes:
        return asyncio.run(self.dispatcher.dispatch(list(parts)))[0]

    def test_commands_and_errors(self) -> None:
        self.assertEqual(self.run(b"PING"), b"+PONG\r\n")
        self.assertEqual(self.run(b"GET"), b"-ERR wrong number of arguments for 'get' command\r\n")
        self.assertEqual(self.run(b"set", b"k", b"v"), b"+OK\r\n")
        self.assertEqual(self.run(b"GET", b"k"), b"$1\r\nv\r\n")
        self.assertEqual(self.run(b"NOPE"), b"-ERR unknown command 'NOPE'\r\n")
