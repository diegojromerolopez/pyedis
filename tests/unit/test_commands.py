import tempfile
import unittest
from src.commands import Commands
from src.persistence import AOF
from src.store import Store

class CommandTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(); self.commands = Commands(Store(), AOF(self.temp.name, False))
    def tearDown(self) -> None: self.temp.cleanup()
    def test_ping_set_get(self) -> None:
        self.assertEqual(self.commands.run([b'PING'])[0], b'+PONG\r\n')
        self.commands.run([b'SET', b'k', b'v'])
        self.assertEqual(self.commands.run([b'GET', b'k'])[0], b'$1\r\nv\r\n')
