"""Command dispatcher characterization tests."""

import unittest

from src.commands import CommandDispatcher
from src.store import Store


class TestCommands(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.store = Store()
        self.dispatcher = CommandDispatcher(self.store)

    async def test_command_names_are_case_insensitive(self) -> None:
        response, close = await self.dispatcher.dispatch([b"pInG"])

        self.assertEqual(response, b"+PONG\r\n")
        self.assertFalse(close)

    async def test_ping_with_payload_returns_bulk_string(self) -> None:
        response, close = await self.dispatcher.dispatch([b"PING", b"hello"])

        self.assertEqual(response, b"$5\r\nhello\r\n")
        self.assertFalse(close)

    async def test_set_and_get_execute_against_store(self) -> None:
        response, close = await self.dispatcher.dispatch([b"set", b"foo", b"bar"])
        self.assertEqual(response, b"+OK\r\n")
        self.assertFalse(close)

        response, close = await self.dispatcher.dispatch([b"GET", b"foo"])
        self.assertEqual(response, b"$3\r\nbar\r\n")
        self.assertFalse(close)
        self.assertEqual(self.store.get("foo"), "bar")

    async def test_arity_errors_use_err_prefix_and_exact_message(self) -> None:
        cases = (
            ([b"ECHO"], b"-ERR wrong number of arguments for 'echo' command\r\n"),
            ([b"GET"], b"-ERR wrong number of arguments for 'get' command\r\n"),
            ([b"SET", b"key"], b"-ERR wrong number of arguments for 'set' command\r\n"),
            ([b"DEL"], b"-ERR wrong number of arguments for 'del' command\r\n"),
        )
        for command, expected in cases:
            with self.subTest(command=command):
                response, close = await self.dispatcher.dispatch(command)
                self.assertEqual(response, expected)
                self.assertFalse(close)

    async def test_unknown_command_returns_err_envelope(self) -> None:
        response, close = await self.dispatcher.dispatch([b"NoSuchCommand"])

        self.assertEqual(response, b"-ERR unknown command 'NOSUCHCOMMAND'\r\n")
        self.assertFalse(close)

    async def test_empty_command_returns_err_envelope(self) -> None:
        response, close = await self.dispatcher.dispatch([])

        self.assertEqual(response, b"-ERR empty command\r\n")
        self.assertFalse(close)

    async def test_quit_returns_ok_and_closes(self) -> None:
        response, close = await self.dispatcher.dispatch([b"QUIT"])

        self.assertEqual(response, b"+OK\r\n")
        self.assertTrue(close)


if __name__ == "__main__":
    unittest.main()
