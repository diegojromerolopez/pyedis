"""Unit tests for persistence engine."""

import os
import tempfile
import unittest
from src.persistence import AOFLogger, replay_aof
from src.store import Store


class TestPersistence(unittest.TestCase):
    def test_aof_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_path = os.path.join(tmpdir, "dump.aof")
            logger = AOFLogger(aof_path, fsync=False)
            logger.log_mutation({"op": "SET", "key": "k", "value": "v"})
            logger.close()

            new_store = Store()
            replayed = replay_aof(aof_path, new_store)
            self.assertEqual(replayed, 1)
            self.assertEqual(new_store.get("k"), "v")


if __name__ == "__main__":
    unittest.main()
