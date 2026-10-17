"""Command dispatcher tests."""
import unittest
from src.commands import CommandDispatcher
from src.store import Store

class TestCommands(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.store = Store()
        self.dispatcher = CommandDispatcher(self.store)

    async def test_ping(self) -> None:
        resp, close = await self.dispatcher.dispatch([b"PING"])
        self.assertEqual(resp, b"+OK\r\n")
        self.assertFalse(close)

    async def test_set_get(self) -> None:
        resp, _ = await self.dispatcher.dispatch([b"SET", b"foo", b"bar"])
        self.assertEqual(resp, b"+OK\r\n")
        resp, _ = await self.dispatcher.dispatch([b"GET", b"foo"])
        self.assertEqual(resp, b"$3\r\nbar\r\n")

if __name__ == "__main__":
    unittest.main()
