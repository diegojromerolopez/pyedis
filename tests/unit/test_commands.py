import unittest

from src.commands import CommandDispatcher
from src.store import Store


class TestCommands(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.store = Store()
        self.dispatcher = CommandDispatcher(self.store)

    async def test_set_and_get(self) -> None:
        res = await self.dispatcher.dispatch([b"SET", b"key1", b"val1"])
        self.assertEqual(res, b"+OK\r\n")

        res = await self.dispatcher.dispatch([b"GET", b"key1"])
        self.assertEqual(res, b"$4\r\nval1\r\n")

    async def test_get_nonexistent(self) -> None:
        res = await self.dispatcher.dispatch([b"GET", b"key_missing"])
        self.assertEqual(res, b"$-1\r\n")

    async def test_exists(self) -> None:
        await self.dispatcher.dispatch([b"SET", b"k1", b"v1"])
        await self.dispatcher.dispatch([b"SET", b"k2", b"v2"])

        res = await self.dispatcher.dispatch([b"EXISTS", b"k1", b"k2", b"k3"])
        self.assertEqual(res, b":2\r\n")

    async def test_del(self) -> None:
        await self.dispatcher.dispatch([b"SET", b"k1", b"v1"])
        await self.dispatcher.dispatch([b"SET", b"k2", b"v2"])

        res = await self.dispatcher.dispatch([b"DEL", b"k1", b"k3"])
        self.assertEqual(res, b":1\r\n")

        res = await self.dispatcher.dispatch([b"GET", b"k1"])
        self.assertEqual(res, b"$-1\r\n")

    async def test_arity_errors(self) -> None:
        res = await self.dispatcher.dispatch([b"GET"])
        self.assertEqual(res, b"-ERR wrong number of arguments for 'get' command\r\n")

        res = await self.dispatcher.dispatch([b"GET", b"a", b"b"])
        self.assertEqual(res, b"-ERR wrong number of arguments for 'get' command\r\n")

        res = await self.dispatcher.dispatch([b"SET", b"a"])
        self.assertEqual(res, b"-ERR wrong number of arguments for 'set' command\r\n")

        res = await self.dispatcher.dispatch([b"DEL"])
        self.assertEqual(res, b"-ERR wrong number of arguments for 'del' command\r\n")

        res = await self.dispatcher.dispatch([b"EXISTS"])
        self.assertEqual(
            res, b"-ERR wrong number of arguments for 'exists' command\r\n"
        )


if __name__ == "__main__":
    unittest.main()
