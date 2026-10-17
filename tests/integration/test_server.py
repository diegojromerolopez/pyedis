"""Integration tests with live TCP socket."""
import asyncio
import tempfile
import unittest
from src.main import run_server

class TestServerIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.port = 6389
        self.server_task = asyncio.create_task(
            run_server(host="127.0.0.1", port=self.port, data_dir=self.tmpdir.name, fsync=False)
        )
        await asyncio.sleep(0.1)

    async def asyncTearDown(self) -> None:
        self.server_task.cancel()
        self.tmpdir.cleanup()

    async def test_ping_over_tcp(self) -> None:
        reader, writer = await asyncio.open_connection("127.0.0.1", self.port)
        writer.write(b"PING\r\n")
        await writer.drain()
        data = await reader.read(100)
        self.assertEqual(data, b"+PONG\r\n")
        writer.close()
        await writer.wait_closed()

if __name__ == "__main__":
    unittest.main()
