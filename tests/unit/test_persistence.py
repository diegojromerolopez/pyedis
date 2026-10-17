"""Characterization tests for append-only-file persistence."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from src.persistence import AOFLogger, replay_aof
from src.store import Store


class TestPersistence(unittest.TestCase):
    def test_log_mutation_appends_json_lines_and_creates_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_file = os.path.join(tmpdir, "nested", "dump.aof")
            logger = AOFLogger(aof_file, fsync=False)

            logger.log_mutation({"op": "SET", "key": "k1", "value": "v1"})
            logger.log_mutation({"op": "DEL", "key": "k2"})

            with open(aof_file, encoding="utf-8") as stream:
                lines = stream.readlines()
            self.assertEqual(
                [json.loads(line) for line in lines],
                [
                    {"op": "SET", "key": "k1", "value": "v1"},
                    {"op": "DEL", "key": "k2"},
                ],
            )

    def test_log_mutation_fsyncs_only_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            enabled_file = os.path.join(tmpdir, "enabled.aof")
            disabled_file = os.path.join(tmpdir, "disabled.aof")
            with patch("src.persistence.os.fsync") as fsync:
                AOFLogger(enabled_file, fsync=True).log_mutation({"op": "SET"})
                self.assertEqual(fsync.call_count, 1)

                AOFLogger(disabled_file, fsync=False).log_mutation({"op": "SET"})
                self.assertEqual(fsync.call_count, 1)

    def test_truncate_empties_existing_aof(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_file = os.path.join(tmpdir, "dump.aof")
            logger = AOFLogger(aof_file, fsync=False)
            logger.log_mutation({"op": "SET", "key": "k", "value": "v"})
            self.assertGreater(os.path.getsize(aof_file), 0)

            logger.truncate()

            self.assertEqual(os.path.getsize(aof_file), 0)

    def test_truncate_does_nothing_for_missing_aof(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AOFLogger(os.path.join(tmpdir, "missing.aof"), fsync=False)
            logger.truncate()
            self.assertFalse(logger.filepath.exists())

    def test_replay_valid_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_file = os.path.join(tmpdir, "dump.aof")
            records = [
                {"op": "SET", "key": "k", "value": "v", "expire_at": 5000.0},
                {"op": "EXPIRE", "key": "k", "expire_at": 6000.0},
                {"op": "DEL", "key": "absent"},
                {"op": "FLUSHALL"},
            ]
            with open(aof_file, "w", encoding="utf-8") as stream:
                stream.write("".join(json.dumps(record) + "\n" for record in records))

            store = Store()
            self.assertEqual(replay_aof(aof_file, store), 4)
            self.assertIsNone(store.get("k"))

    def test_replay_missing_file_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Store()
            self.assertEqual(replay_aof(os.path.join(tmpdir, "missing.aof"), store), 0)

    def test_replay_ignores_corrupt_and_truncated_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_file = os.path.join(tmpdir, "dump.aof")
            with open(aof_file, "w", encoding="utf-8") as stream:
                stream.write(json.dumps({"op": "SET", "key": "good", "value": "yes"}) + "\n")
                stream.write('{"op":"SET","key":"corrupt"\n')
                stream.write('{"op":"SET","key":"truncated"')

            store = Store()
            self.assertEqual(replay_aof(aof_file, store), 1)
            self.assertEqual(store.get("good"), "yes")
            self.assertIsNone(store.get("corrupt"))
            self.assertIsNone(store.get("truncated"))


if __name__ == "__main__":
    unittest.main()
