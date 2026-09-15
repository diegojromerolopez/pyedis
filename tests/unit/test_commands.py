import tempfile
import unittest
from src.commands import Commands
from src.persistence import Persistence
from src.store import Store

class CommandsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(); p = Persistence(self.directory.name, False); p.open(); self.c = Commands(Store(), p)
    def tearDown(self) -> None: self.directory.cleanup()
    def test_set_get_incr(self) -> None:
        self.assertEqual(self.c.execute([b"SET", b"x", b"1"])[0], "OK")
        self.assertEqual(self.c.execute([b"INCR", b"x"])[0], 2)
        self.assertEqual(self.c.execute([b"GET", b"x"])[0], b"2")
