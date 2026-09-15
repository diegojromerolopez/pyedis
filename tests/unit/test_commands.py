import unittest
from tempfile import TemporaryDirectory
from src.commands import Commands
from src.persistence import AOF
from src.store import Store


class CommandTests(unittest.TestCase):
    def test_ping_set_get(self) -> None:
        with TemporaryDirectory() as directory:
            command = Commands(Store(), AOF(directory, False))
            self.assertEqual(command.run([b"PING"])[0], b"+PONG\r\n")
            self.assertEqual(command.run([b"SET", b"x", b"value"])[0], b"+OK\r\n")
            self.assertEqual(command.run([b"GET", b"x"])[0], b"$5\r\nvalue\r\n")
