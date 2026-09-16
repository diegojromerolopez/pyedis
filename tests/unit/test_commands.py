import tempfile
import unittest
from src.commands import Dispatcher
from src.persistence import AOF
from src.store import Store


class CommandTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.dispatcher = Dispatcher(Store(), AOF(self.directory.name, False))

    async def asyncTearDown(self) -> None:
        self.directory.cleanup()

    async def test_set_get_and_errors(self) -> None:
        reply, _ = await self.dispatcher.execute([b"set", b"k", b"v"])
        self.assertEqual(reply, b"+OK\r\n")
        reply, _ = await self.dispatcher.execute([b"GET", b"k"])
        self.assertEqual(reply, b"$1\r\nv\r\n")
        reply, _ = await self.dispatcher.execute([b"GET"])
        self.assertIn(b"wrong number", reply)

    async def test_nx(self) -> None:
        first, _ = await self.dispatcher.execute([b"SET", b"k", b"v", b"NX"])
        second, _ = await self.dispatcher.execute([b"SET", b"k", b"v", b"NX"])
        self.assertEqual(first, b"+OK\r\n")
        self.assertEqual(second, b"$-1\r\n")
