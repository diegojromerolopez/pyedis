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


if __name__ == "__main__":
    unittest.main()
