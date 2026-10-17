"""Unit tests for command dispatcher."""

import unittest

from src.commands import CommandDispatcher
from src.store import Store


class RecordingAOF:
    """In-memory persistence double recording the dispatcher boundary calls."""

    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []
        self.truncated = False

    def log_mutation(self, record: dict[str, object]) -> None:
        self.records.append(record)

    def truncate(self) -> None:
        self.truncated = True


class TestCommands(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.store = Store()
        self.aof = RecordingAOF()
        self.dispatcher = CommandDispatcher(self.store, self.aof)  # type: ignore[arg-type]

    async def test_ping(self) -> None:
        reply, close = await self.dispatcher.dispatch([b"PING"])
        self.assertEqual(reply, b"+PONG\r\n")
        self.assertFalse(close)

    async def test_set_get_and_aof_recording(self) -> None:
        reply, close = await self.dispatcher.dispatch([b"SET", b"foo", b"bar"])
        self.assertEqual((reply, close), (b"+OK\r\n", False))
        self.assertEqual(
            self.aof.records, [{"op": "SET", "key": "foo", "value": "bar", "expire_at": None}]
        )

        reply, _ = await self.dispatcher.dispatch([b"GET", b"foo"])
        self.assertEqual(reply, b"$3\r\nbar\r\n")

    async def test_mutating_commands_record_only_successful_changes(self) -> None:
        await self.dispatcher.dispatch([b"SET", b"count", b"1"])
        reply, _ = await self.dispatcher.dispatch([b"INCR", b"count"])
        self.assertEqual(reply, b":2\r\n")
        reply, _ = await self.dispatcher.dispatch([b"DEL", b"count"])
        self.assertEqual(reply, b":1\r\n")
        self.assertEqual([record["op"] for record in self.aof.records], ["SET", "INCR", "DEL"])

    async def test_command_arity_errors(self) -> None:
        cases = [
            ([b"ECHO"], b"echo"),
            ([b"ECHO", b"one", b"two"], b"echo"),
            ([b"SET", b"key"], b"set"),
            ([b"GET"], b"get"),
            ([b"GET", b"key", b"extra"], b"get"),
            ([b"DEL"], b"del"),
            ([b"EXISTS"], b"exists"),
            ([b"INCR"], b"incr"),
            ([b"DECR", b"a", b"b"], b"decr"),
            ([b"EXPIRE", b"key"], b"expire"),
            ([b"TTL"], b"ttl"),
            ([b"KEYS"], b"keys"),
        ]
        for args, command in cases:
            with self.subTest(args=args):
                reply, close = await self.dispatcher.dispatch(args)
                self.assertEqual(
                    reply, b"-ERR wrong number of arguments for '" + command + b"' command\r\n"
                )
                self.assertFalse(close)

    async def test_set_syntax_error_does_not_mutate_or_log(self) -> None:
        reply, _ = await self.dispatcher.dispatch([b"SET", b"key", b"value", b"EX"])
        self.assertEqual(reply, b"-ERR syntax error\r\n")
        self.assertIsNone(self.store.get("key"))
        self.assertEqual(self.aof.records, [])

    async def test_quit_requests_connection_close(self) -> None:
        reply, close = await self.dispatcher.dispatch([b"QUIT"])
        self.assertEqual(reply, b"+OK\r\n")
        self.assertTrue(close)

    async def test_flushall_truncates_aof(self) -> None:
        await self.dispatcher.dispatch([b"SET", b"key", b"value"])
        reply, _ = await self.dispatcher.dispatch([b"FLUSHALL"])
        self.assertEqual(reply, b"+OK\r\n")
        self.assertIsNone(self.store.get("key"))
        self.assertTrue(self.aof.truncated)


if __name__ == "__main__":
    unittest.main()
