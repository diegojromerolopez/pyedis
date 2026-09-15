import tempfile
import unittest
from src.persistence import Persistence
from src.store import Store

class PersistenceTest(unittest.TestCase):
    def test_replay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            p = Persistence(directory, False); p.open(); p.append({'op':'SET','key':'a','value':'b','expire_at':None})
            s = Store(); p.replay(s, lambda _: None); self.assertEqual(s.get(b'a'), b'b')
