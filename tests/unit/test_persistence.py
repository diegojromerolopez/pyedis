import unittest
import tempfile
import shutil
from src.store import Store
from src.persistence import AOFLogger


class TestPersistence(unittest.TestCase):
    def setUp(self) -> None:
        self.data_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.data_dir)

    def test_replay(self) -> None:
        aof = AOFLogger(self.data_dir, fsync=False)
        aof.append({"op": "SET", "key": "k", "value": "v"})
        aof.close()

        store = Store()
        aof2 = AOFLogger(self.data_dir, fsync=False)
        aof2.replay(store)
        self.assertEqual(store.get("k"), "v")
        aof2.close()


if __name__ == "__main__":
    unittest.main()
