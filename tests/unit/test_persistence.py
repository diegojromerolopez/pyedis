import unittest
from tempfile import TemporaryDirectory
from src.persistence import AOF
from src.store import Store


class PersistenceTests(unittest.TestCase):
    def test_replay(self) -> None:
        with TemporaryDirectory() as directory:
            aof = AOF(directory, False); aof.append({"op":"SET","key":"x","value":"y","expire_at":None})
            store = Store(); aof.replay(store)
            self.assertEqual(store.get("x").value, "y")
