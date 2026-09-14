import os
import shutil
import tempfile
import unittest
from src.persistence import AOFLogger
from src.store import Store


class TestPersistence(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)

    def test_aof_roundtrip_and_corruption(self) -> None:
        aof = AOFLogger(self.test_dir, fsync=False)
        aof.log({"op": "SET", "key": "k1", "value": "v1", "expire_at": None})
        aof.log({"op": "INCR", "key": "c"})
        with open(aof.filepath, "a", encoding="utf-8") as f:
            f.write('{"op":"SET","key":"corrupted_line')

        store = Store()
        aof.replay(store)
        self.assertEqual(store.get("k1"), b"v1")
        self.assertEqual(store.get("c"), b"1")


if __name__ == "__main__":
    unittest.main()
