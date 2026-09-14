import unittest
from src.commands import CommandDispatcher
from src.store import Store


class TestCommands(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.time = 1000.0
        self.store = Store(clock=lambda: self.time)
        self.dispatcher = CommandDispatcher(self.store, clock=lambda: self.time)

    async def test_ping(self) -> None:
        res, close = await self.dispatcher.dispatch([b"PING"])
        self.assertEqual(res, b"+PONG\r\n")
        self.assertFalse(close)

    async def test_set_nx_xx(self) -> None:
        res, _ = await self.dispatcher.dispatch([b"SET", b"k", b"v", b"NX"])
        self.assertEqual(res, b"+OK\r\n")
        res, _ = await self.dispatcher.dispatch([b"SET", b"k", b"v", b"NX"])
        self.assertEqual(res, b"$-1\r\n")
        res, _ = await self.dispatcher.dispatch([b"SET", b"k", b"v", b"XX"])
        self.assertEqual(res, b"+OK\r\n")

    async def test_arity_error(self) -> None:
        res, _ = await self.dispatcher.dispatch([b"GET"])
        self.assertIn(b"-ERR wrong number of arguments", res)


if __name__ == "__main__":
    unittest.main()
