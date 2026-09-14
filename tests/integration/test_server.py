import unittest
import asyncio
import tempfile
import shutil
import redis
from src.store import Store
from src.persistence import AOFLogger
from src.commands import CommandDispatcher
from src.main import handle_client


class TestServerIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.data_dir = tempfile.mkdtemp()
        self.store = Store()
        self.aof = AOFLogger(self.data_dir, fsync=False)
        self.dispatcher = CommandDispatcher(self.store, self.aof)
        self.server = await asyncio.start_server(
            lambda r, w: handle_client(r, w, self.dispatcher),
            "127.0.0.1",
            0,
        )
        self.port = self.server.sockets[0].getsockname()[1]

    async def asyncTearDown(self) -> None:
        self.server.close()
        await self.server.wait_closed()
        self.aof.close()
        shutil.rmtree(self.data_dir)

    async def test_redis_py_client(self) -> None:
        client = redis.Redis(host="127.0.0.1", port=self.port, socket_timeout=2.0)
        self.assertTrue(client.ping())
        client.set("foo", "bar")
        self.assertEqual(client.get("foo"), b"bar")
        client.close()


if __name__ == "__main__":
    unittest.main()
