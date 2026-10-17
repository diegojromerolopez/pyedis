"""Command dispatcher characterization tests."""

import unittest

from src.commands import CommandDispatcher
from src.store import Store


class TestCommands(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        # Store is the in-memory test double used by the dispatcher.
        self.store = Store()
        self.dispatcher = CommandDispatcher(self.store)

    async def test_ping_is_case_insensitive_and_returns_simple_string(self) -> None:
        response, close = await self.dispatcher.dispatch([b"pInG"])

        self.assertEqual(response, b"+PONG\r\n")
    async def test_ping(self) -> None:
        resp, close = await self.dispatcher.dispatch([b"PING"])
        self.assertEqual(resp, b"+PONG\r\n")
        self.assertFalse(close)

    async def test_ping_with_payload_returns_bulk_string(self) -> None:
        response, close = await self.dispatcher.dispatch([b"PING", b"hello"])

        self.assertEqual(response, b"$5\r\nhello\r\n")
        self.assertFalse(close)

    async def test_set_and_get_are_case_insensitive_and_mutate_store(self) -> None:
        response, close = await self.dispatcher.dispatch([b"sEt", b"foo", b"bar"])
        self.assertEqual(response, b"+OK\r\n")
        self.assertFalse(close)

        response, close = await self.dispatcher.dispatch([b"GeT", b"foo"])
        self.assertEqual(response, b"$3\r\nbar\r\n")
        self.assertFalse(close)
        self.assertEqual(self.store.get("foo"), "bar")

    async def test_get_missing_key_returns_null_bulk_string(self) -> None:
        response, close = await self.dispatcher.dispatch([b"GET", b"missing"])

        self.assertEqual(response, b"$-1\r\n")
        self.assertFalse(close)

    async def test_echo_requires_exactly_one_argument(self) -> None:
        for args in ([b"ECHO"], [b"ECHO", b"one", b"two"]):
            with self.subTest(args=args):
                response, close = await self.dispatcher.dispatch(list(args))
                self.assertEqual(
                    response,
                    b"-ERR wrong number of arguments for 'echo' command\r\n",
                )
                self.assertFalse(close)

    async def test_command_arity_errors_have_expected_error_prefix(self) -> None:
        cases = (
            ([b"SET"], b"-ERR wrong number of arguments for 'set' command\r\n"),
            ([b"SET", b"key"], b"-ERR wrong number of arguments for 'set' command\r\n"),
            ([b"GET"], b"-ERR wrong number of arguments for 'get' command\r\n"),
            ([b"GET", b"key", b"extra"], b"-ERR wrong number of arguments for 'get' command\r\n"),
            ([b"DEL"], b"-ERR wrong number of arguments for 'del' command\r\n"),
            ([b"EXISTS"], b"-ERR wrong number of arguments for 'exists' command\r\n"),
            ([b"INCR"], b"-ERR wrong number of arguments for 'incr' command\r\n"),
            ([b"DECR", b"a", b"b"], b"-ERR wrong number of arguments for 'decr' command\r\n"),
            ([b"TTL"], b"-ERR wrong number of arguments for 'ttl' command\r\n"),
            ([b"EXPIRE", b"key"], b"-ERR wrong number of arguments for 'expire' command\r\n"),
            ([b"KEYS"], b"-ERR wrong number of arguments for 'keys' command\r\n"),
        )

        for args, expected in cases:
            with self.subTest(args=args):
                response, close = await self.dispatcher.dispatch(args)
                self.assertEqual(response, expected)
                self.assertFalse(close)

    async def test_empty_and_unknown_commands_return_error_envelopes(self) -> None:
        response, close = await self.dispatcher.dispatch([])
        self.assertEqual(response, b"-ERR empty command\r\n")
        self.assertFalse(close)

        response, close = await self.dispatcher.dispatch([b"NoSuchCommand"])
        self.assertEqual(response, b"-ERR unknown command 'NOSUCHCOMMAND'\r\n")
        self.assertFalse(close)

    async def test_mutating_commands_execute_against_the_in_memory_store(self) -> None:
        response, _ = await self.dispatcher.dispatch([b"SET", b"counter", b"10"])
        self.assertEqual(response, b"+OK\r\n")

        response, _ = await self.dispatcher.dispatch([b"INCR", b"counter"])
        self.assertEqual(response, b":11\r\n")
        response, _ = await self.dispatcher.dispatch([b"DECR", b"counter"])
        self.assertEqual(response, b":10\r\n")

        response, _ = await self.dispatcher.dispatch([b"EXISTS", b"counter", b"missing"])
        self.assertEqual(response, b":1\r\n")
        response, _ = await self.dispatcher.dispatch([b"DEL", b"counter"])
        self.assertEqual(response, b":1\r\n")
        response, _ = await self.dispatcher.dispatch([b"GET", b"counter"])
        self.assertEqual(response, b"$-1\r\n")

    async def test_quit_returns_ok_and_requests_connection_close(self) -> None:
        response, close = await self.dispatcher.dispatch([b"qUiT"])

        self.assertEqual(response, b"+OK\r\n")
        self.assertTrue(close)




if __name__ == "__main__":
    unittest.main()
