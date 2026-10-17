"""Live server socket tests."""
import asyncio
import tempfile
import unittest
from src.main import run_server

class TestServerIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.port = 16379
        self.server_task = asyncio.create_task(
            run_server(host="127.0.0.1", port=self.port, data_dir=self.tmpdir.name, fsync=False)
        )
        await asyncio.sleep(0.1)

    async def asyncTearDown(self) -> None:
        self.server_task.cancel()
        try:
            await self.server_task
        except asyncio.CancelledError:
            pass
        self.tmpdir.cleanup()

    async def test_socket_ping(self) -> None:
        reader, writer = await asyncio.open_connection("127.0.0.1", self.port)
        writer.write(b"PING\r\n")
        await writer.drain()
        response = await reader.read(100)
        self.assertEqual(response, b"+OK\r\n")
        writer.close()
        await writer.wait_closed()

if __name__ == "__main__":
    unittest.main()
