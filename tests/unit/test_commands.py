"""Unit tests for command dispatcher."""
import unittest
from src.commands import CommandDispatcher
from src.store import Store

class TestCommands(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.store = Store()
        self.dispatcher = CommandDispatcher(self.store)

    async def test_ping(self) -> None:
        reply, close = await self.dispatcher.dispatch([b"PING"])
        self.assertEqual(reply, b"+PONG\r\n")
        self.assertFalse(close)

    async def test_set_get(self) -> None:
        await self.dispatcher.dispatch([b"SET", b"foo", b"bar"])
        reply, _ = await self.dispatcher.dispatch([b"GET", b"foo"])
        self.assertEqual(reply, b"$3\r\nbar\r\n")

if __name__ == "__main__":
    unittest.main()
