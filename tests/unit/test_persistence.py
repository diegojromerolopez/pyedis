"""Unit and integration tests for the persistence engine."""

import json
import os
import tempfile
import unittest

from src.commands import CommandDispatcher
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

    def test_replay_stops_at_trailing_corrupt_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_path = os.path.join(tmpdir, "dump.aof")
            with open(aof_path, "w", encoding="utf-8") as aof:
                aof.write(json.dumps({"op": "SET", "key": "before", "value": "yes"}) + "\n")
                aof.write('{"op":"SET","key":"broken"\n')
                aof.write(json.dumps({"op": "SET", "key": "after", "value": "no"}) + "\n")

            store = Store()
            self.assertEqual(replay_aof(aof_path, store), 1)
            self.assertEqual(store.get("before"), "yes")
            self.assertIsNone(store.get("after"))

    def test_dispatcher_aof_can_be_replayed_into_a_new_store(self) -> None:
        async def scenario() -> None:
            with tempfile.TemporaryDirectory() as tmpdir:
                path = os.path.join(tmpdir, "dump.aof")
                logger = AOFLogger(path, fsync=False)
                source = Store()
                dispatcher = CommandDispatcher(source, logger)
                await dispatcher.dispatch([b"SET", b"counter", b"1"])
                await dispatcher.dispatch([b"INCR", b"counter"])
                await dispatcher.dispatch([b"DEL", b"counter"])
                logger.close()

                restored = Store()
                self.assertEqual(replay_aof(path, restored), 3)
                self.assertIsNone(restored.get("counter"))

        import asyncio

        asyncio.run(scenario())

    def test_replay_missing_file_returns_zero(self) -> None:
        store = Store()
        replayed = replay_aof("/nonexistent/path/does-not-exist.aof", store)
        self.assertEqual(replayed, 0)

    def test_replay_honours_absolute_expiry_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_path = os.path.join(tmpdir, "dump.aof")
            future_ts = 9999999999.0
            past_ts = 1.0
            with open(aof_path, "w", encoding="utf-8") as aof:
                aof.write(
                    json.dumps(
                        {"op": "SET", "key": "future", "value": "alive", "expire_at": future_ts}
                    )
                    + "\n"
                )
                aof.write(
                    json.dumps({"op": "SET", "key": "past", "value": "dead", "expire_at": past_ts})
                    + "\n"
                )

            store = Store()
            replayed = replay_aof(aof_path, store)
            self.assertEqual(replayed, 2)
            self.assertEqual(store.get("future"), "alive")
            self.assertIsNone(store.get("past"))

    def test_replay_applies_expire_op_as_absolute_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_path = os.path.join(tmpdir, "dump.aof")
            future_ts = 9999999999.0
            with open(aof_path, "w", encoding="utf-8") as aof:
                aof.write(json.dumps({"op": "SET", "key": "k", "value": "v"}) + "\n")
                aof.write(json.dumps({"op": "EXPIRE", "key": "k", "expire_at": future_ts}) + "\n")

            store = Store()
            replayed = replay_aof(aof_path, store)
            self.assertEqual(replayed, 2)
            self.assertEqual(store.get("k"), "v")
            self.assertGreater(store.ttl("k"), 0)

    def test_replay_applies_flushall_op(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_path = os.path.join(tmpdir, "dump.aof")
            with open(aof_path, "w", encoding="utf-8") as aof:
                aof.write(json.dumps({"op": "SET", "key": "a", "value": "1"}) + "\n")
                aof.write(json.dumps({"op": "SET", "key": "b", "value": "2"}) + "\n")
                aof.write(json.dumps({"op": "FLUSHALL"}) + "\n")
                aof.write(json.dumps({"op": "SET", "key": "c", "value": "3"}) + "\n")

            store = Store()
            replayed = replay_aof(aof_path, store)
            self.assertEqual(replayed, 4)
            self.assertIsNone(store.get("a"))
            self.assertIsNone(store.get("b"))
            self.assertEqual(store.get("c"), "3")

    def test_replay_applies_decr_op(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_path = os.path.join(tmpdir, "dump.aof")
            with open(aof_path, "w", encoding="utf-8") as aof:
                aof.write(json.dumps({"op": "SET", "key": "n", "value": "5"}) + "\n")
                aof.write(json.dumps({"op": "DECR", "key": "n"}) + "\n")
                aof.write(json.dumps({"op": "DECR", "key": "n"}) + "\n")

            store = Store()
            replayed = replay_aof(aof_path, store)
            self.assertEqual(replayed, 3)
            self.assertEqual(store.get("n"), "3")

    def test_corrupt_line_before_end_halts_replay_of_subsequent_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_path = os.path.join(tmpdir, "dump.aof")
            with open(aof_path, "w", encoding="utf-8") as aof:
                aof.write(json.dumps({"op": "SET", "key": "first", "value": "ok"}) + "\n")
                aof.write("not even json {{{\n")
                aof.write(json.dumps({"op": "SET", "key": "second", "value": "ok"}) + "\n")
                aof.write(json.dumps({"op": "SET", "key": "third", "value": "ok"}) + "\n")

            store = Store()
            replayed = replay_aof(aof_path, store)
            self.assertEqual(replayed, 1)
            self.assertEqual(store.get("first"), "ok")
            self.assertIsNone(store.get("second"))
            self.assertIsNone(store.get("third"))

    def test_logger_truncate_clears_prior_records_from_future_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_path = os.path.join(tmpdir, "dump.aof")
            logger = AOFLogger(aof_path, fsync=False)
            logger.log_mutation({"op": "SET", "key": "stale", "value": "old"})
            logger.truncate()
            logger.log_mutation({"op": "SET", "key": "fresh", "value": "new"})
            logger.close()

            store = Store()
            replayed = replay_aof(aof_path, store)
            self.assertEqual(replayed, 1)
            self.assertIsNone(store.get("stale"))
            self.assertEqual(store.get("fresh"), "new")

    def test_blank_lines_between_records_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            aof_path = os.path.join(tmpdir, "dump.aof")
            with open(aof_path, "w", encoding="utf-8") as aof:
                aof.write("\n")
                aof.write(json.dumps({"op": "SET", "key": "k", "value": "v"}) + "\n")
                aof.write("   \n")

            store = Store()
            replayed = replay_aof(aof_path, store)
            self.assertEqual(replayed, 1)
            self.assertEqual(store.get("k"), "v")


if __name__ == "__main__":
    unittest.main()
