import unittest
import tempfile
import shutil
from src.store import Store
from src.persistence import AOFLogger
from src.commands import CommandDispatcher


class TestCommands(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.data_dir = tempfile.mkdtemp()
        self.store = Store()
        self.aof = AOFLogger(self.data_dir, fsync=False)
        self.dispatcher = CommandDispatcher(self.store, self.aof)

    async def asyncTearDown(self) -> None:
        self.aof.close()
        shutil.rmtree(self.data_dir)

    async def test_ping(self) -> None:
        res, close = await self.dispatcher.dispatch([b"PING"])
        self.assertEqual(res, b"+PONG\r\n")
        self.assertFalse(close)

    async def test_set_get(self) -> None:
        res, _ = await self.dispatcher.dispatch([b"SET", b"key", b"val"])
        self.assertEqual(res, b"+OK\r\n")
        res, _ = await self.dispatcher.dispatch([b"GET", b"key"])
        self.assertEqual(res, b"$3\r\nval\r\n")


if __name__ == "__main__":
    unittest.main()
