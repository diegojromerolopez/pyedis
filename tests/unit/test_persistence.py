"""AOF Persistence tests."""
import os
import tempfile
import unittest
from src.persistence import AOFLogger, replay_aof
from src.store import Store

class TestPersistence(unittest.TestCase):
    def test_aof_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_file = os.path.join(tmpdir, "dump.aof")
            logger = AOFLogger(aof_file, fsync=False)
            logger.log_mutation({"op": "SET", "key": "k1", "value": "v1", "expire_at": None})
            
            store = Store()
            replayed = replay_aof(aof_file, store)
            self.assertEqual(replayed, 1)
            self.assertEqual(store.get("k1"), "v1")

if __name__ == "__main__":
    unittest.main()
