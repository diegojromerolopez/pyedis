import tempfile
import unittest
from src.persistence import AOF
from src.store import Store

class PersistenceTest(unittest.TestCase):
    def test_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            aof = AOF(directory, False); aof.append({'op':'SET','key':'k','value':'v','expire_at':None})
            store = Store(); aof.load(store); self.assertEqual(store.get(b'k'), b'v')
