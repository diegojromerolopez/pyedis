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

    async def test_set_options_ex_px_nx_xx(self) -> None:
        # NX on missing key -> OK
        res = await self.dispatcher.dispatch([b"SET", b"k1", b"v1", b"NX"])
        self.assertEqual(res, b"+OK\r\n")

        # NX on existing key -> Null Bulk String
        res = await self.dispatcher.dispatch([b"SET", b"k1", b"v2", b"NX"])
        self.assertEqual(res, b"$-1\r\n")

        # XX on existing key -> OK
        res = await self.dispatcher.dispatch([b"SET", b"k1", b"v2", b"XX"])
        self.assertEqual(res, b"+OK\r\n")

        # XX on missing key -> Null Bulk String
        res = await self.dispatcher.dispatch([b"SET", b"k2", b"v2", b"XX"])
        self.assertEqual(res, b"$-1\r\n")

        # EX option
        res = await self.dispatcher.dispatch([b"SET", b"k3", b"v3", b"EX", b"10"])
        self.assertEqual(res, b"+OK\r\n")

        # PX option
        res = await self.dispatcher.dispatch([b"SET", b"k4", b"v4", b"PX", b"5000"])
        self.assertEqual(res, b"+OK\r\n")

    async def test_set_syntax_and_value_errors(self) -> None:
        res = await self.dispatcher.dispatch(
            [b"SET", b"k1", b"v1", b"EX", b"not_an_int"]
        )
        self.assertEqual(res, b"-ERR value is not an integer or out of range\r\n")

        res = await self.dispatcher.dispatch(
            [b"SET", b"k1", b"v1", b"PX", b"not_an_int"]
        )
        self.assertEqual(res, b"-ERR value is not an integer or out of range\r\n")

        res = await self.dispatcher.dispatch([b"SET", b"k1", b"v1", b"INVALID_OPT"])
        self.assertEqual(res, b"-ERR syntax error\r\n")

    async def test_incr_decr(self) -> None:
        # INCR on missing key -> 1
        res = await self.dispatcher.dispatch([b"INCR", b"counter"])
        self.assertEqual(res, b":1\r\n")

        # INCR on existing key -> 2
        res = await self.dispatcher.dispatch([b"INCR", b"counter"])
        self.assertEqual(res, b":2\r\n")

        # DECR on existing key -> 1
        res = await self.dispatcher.dispatch([b"DECR", b"counter"])
        self.assertEqual(res, b":1\r\n")

        # DECR on missing key -> -1
        res = await self.dispatcher.dispatch([b"DECR", b"missing_counter"])
        self.assertEqual(res, b":-1\r\n")

    async def test_incr_decr_invalid_value(self) -> None:
        await self.dispatcher.dispatch([b"SET", b"str_key", b"abc"])
        res = await self.dispatcher.dispatch([b"INCR", b"str_key"])
        self.assertEqual(res, b"-ERR value is not an integer or out of range\r\n")

        res = await self.dispatcher.dispatch([b"DECR", b"str_key"])
        self.assertEqual(res, b"-ERR value is not an integer or out of range\r\n")

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

        res = await self.dispatcher.dispatch([b"INCR"])
        self.assertEqual(res, b"-ERR wrong number of arguments for 'incr' command\r\n")

        res = await self.dispatcher.dispatch([b"DECR"])
        self.assertEqual(res, b"-ERR wrong number of arguments for 'decr' command\r\n")

        res = await self.dispatcher.dispatch([b"DEL"])
        self.assertEqual(res, b"-ERR wrong number of arguments for 'del' command\r\n")

        res = await self.dispatcher.dispatch([b"EXISTS"])
        self.assertEqual(
            res, b"-ERR wrong number of arguments for 'exists' command\r\n"
        )


if __name__ == "__main__":
    unittest.main()
