import unittest
from src.commands import Dispatcher
from src.resp import Decoder
from src.store import Store


class CommandTest(unittest.IsolatedAsyncioTestCase):
    async def test_commands_and_errors(self) -> None:
        dispatch = Dispatcher(Store())
        reply, _ = await dispatch.execute([b"set", b"k", b"v"])
        self.assertEqual(reply, b"+OK\r\n")
        reply, _ = await dispatch.execute([b"GET", b"k"])
        self.assertEqual(reply, b"$1\r\nv\r\n")
        reply, _ = await dispatch.execute([b"GET"])
        self.assertIn(b"wrong number", reply)
        reply, _ = await dispatch.execute([b"FOO"])
        self.assertEqual(reply, b"-ERR unknown command 'FOO'\r\n")
