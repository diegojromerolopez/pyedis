"""Characterization tests for the append-only persistence engine."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.persistence import AOFLogger, replay_aof
from src.store import Store


class TestAOFLogger(unittest.TestCase):
    def test_log_mutation_creates_parent_and_appends_json_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "dump.aof"
            logger = AOFLogger(path, fsync=False)

            logger.log_mutation({"op": "SET", "key": "first", "value": "one"})
            logger.log_mutation({"op": "DEL", "key": "first"})

            self.assertTrue(path.exists())
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                [json.loads(line) for line in lines],
                [
                    {"op": "SET", "key": "first", "value": "one"},
                    {"op": "DEL", "key": "first"},
                ],
            )

    def test_fsync_is_called_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "dump.aof"
            logger = AOFLogger(path, fsync=True)

            with patch("src.persistence.os.fsync") as fsync:
                logger.log_mutation({"op": "SET", "key": "k", "value": "v"})

            fsync.assert_called_once()
            self.assertGreaterEqual(len(fsync.call_args.args), 1)

    def test_fsync_is_not_called_when_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "dump.aof"
            logger = AOFLogger(path, fsync=False)

            with patch("src.persistence.os.fsync") as fsync:
                logger.log_mutation({"op": "SET", "key": "k", "value": "v"})

            fsync.assert_not_called()

    def test_truncate_removes_existing_records_and_is_safe_if_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "dump.aof"
            logger = AOFLogger(path, fsync=False)
            logger.log_mutation({"op": "SET", "key": "k", "value": "v"})

            logger.truncate()
            self.assertTrue(path.exists())
            self.assertEqual(path.read_bytes(), b"")

            missing_logger = AOFLogger(Path(tmpdir) / "missing.aof", fsync=False)
            missing_logger.truncate()
            self.assertFalse(missing_logger.filepath.exists())


class TestAOFReplay(unittest.TestCase):
    def test_replay_valid_mutations_reconstructs_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "dump.aof"
            path.write_text(
                "\n".join(
                    [
                        json.dumps({"op": "SET", "key": "alpha", "value": "one"}),
                        json.dumps({"op": "SET", "key": "beta", "value": "two"}),
                        json.dumps({"op": "EXPIRE", "key": "alpha", "expire_at": 150.0}),
                        json.dumps({"op": "DEL", "key": "beta"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            store = Store(clock=lambda: 100.0)

            replayed = replay_aof(path, store)

            self.assertEqual(replayed, 4)
            self.assertEqual(store.get("alpha"), "one")
            self.assertEqual(store.ttl("alpha"), 50)
            self.assertIsNone(store.get("beta"))

    def test_replay_flushall_clears_prior_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "dump.aof"
            path.write_text(
                json.dumps({"op": "SET", "key": "k", "value": "v"})
                + "\n"
                + json.dumps({"op": "FLUSHALL"})
                + "\n",
                encoding="utf-8",
            )
            store = Store()

            self.assertEqual(replay_aof(path, store), 2)
            self.assertIsNone(store.get("k"))

    def test_replay_missing_file_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Store()
            store.set("existing", "value")

            replayed = replay_aof(Path(tmpdir) / "does-not-exist.aof", store)

            self.assertEqual(replayed, 0)
            self.assertEqual(store.get("existing"), "value")

    def test_replay_ignores_corrupt_line_and_continues(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "dump.aof"
            path.write_text(
                json.dumps({"op": "SET", "key": "before", "value": "ok"})
                + "\nnot valid json\n"
                + json.dumps({"op": "SET", "key": "after", "value": "also-ok"})
                + "\n",
                encoding="utf-8",
            )
            store = Store()

            replayed = replay_aof(path, store)

            self.assertEqual(replayed, 2)
            self.assertEqual(store.get("before"), "ok")
            self.assertEqual(store.get("after"), "also-ok")

    def test_replay_ignores_truncated_trailing_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "dump.aof"
            path.write_text(
                json.dumps({"op": "SET", "key": "complete", "value": "yes"})
                + "\n"
                + '{"op":"SET","key":"partial","value":"incomplete',
                encoding="utf-8",
            )
            store = Store()

            replayed = replay_aof(path, store)

            self.assertEqual(replayed, 1)
            self.assertEqual(store.get("complete"), "yes")
            self.assertIsNone(store.get("partial"))


if __name__ == "__main__":
    unittest.main()
