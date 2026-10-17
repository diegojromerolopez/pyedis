"""Black-box integration tests for the asyncio TCP server."""

import asyncio
import tempfile
import unittest
from pathlib import Path

from src.main import run_server


class TestServerIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.port = await self._unused_port()
        self.server_task = asyncio.create_task(
            run_server(
                host="127.0.0.1",
                port=self.port,
                data_dir=self.tmpdir.name,
                fsync=False,
            )
        )
        self.reader, self.writer = await self._wait_until_ready()
        self.writer.close()
        await asyncio.wait_for(self.writer.wait_closed(), timeout=2.0)

    async def asyncTearDown(self) -> None:
        self.server_task.cancel()
        try:
            await asyncio.wait_for(self.server_task, timeout=2.0)
        except asyncio.CancelledError:
            pass
        self.tmpdir.cleanup()

    async def _unused_port(self) -> int:
        probe = await asyncio.start_server(lambda _r, w: w.close(), "127.0.0.1", 0)
        port = probe.sockets[0].getsockname()[1]
        probe.close()
        await probe.wait_closed()
        return port

    async def _wait_until_ready(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        deadline = asyncio.get_running_loop().time() + 2.0
        while True:
            try:
                return await asyncio.wait_for(
                    asyncio.open_connection("127.0.0.1", self.port), timeout=2.0
                )
            except (ConnectionRefusedError, OSError):
                if asyncio.get_running_loop().time() >= deadline:
                    self.fail("server did not become ready within 2 seconds")
                await asyncio.sleep(0.01)

    async def _command(self, payload: bytes) -> bytes:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", self.port), timeout=2.0
        )
        try:
            writer.write(payload)
            await asyncio.wait_for(writer.drain(), timeout=2.0)
            return await asyncio.wait_for(reader.read(4096), timeout=2.0)
        finally:
            writer.close()
            await asyncio.wait_for(writer.wait_closed(), timeout=2.0)

    async def test_live_socket_supports_ping_and_pipeline(self) -> None:
        response = await self._command(
            b"*1\r\n$4\r\nPING\r\n*2\r\n$3\r\nSET\r\n$3\r\nkey\r\n"
            b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n"
        )
        self.assertEqual(response, b"+PONG\r\n+OK\r\n$3\r\nkey\r\n")

    async def test_client_disconnect_does_not_stop_server(self) -> None:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", self.port), timeout=2.0
        )
        writer.write(b"*2\r\n$3\r\nSET\r\n$8\r\nbefore\r\n")
        await asyncio.wait_for(writer.drain(), timeout=2.0)
        self.assertEqual(await asyncio.wait_for(reader.readexactly(5), timeout=2.0), b"+OK\r\n")
        writer.close()
        await asyncio.wait_for(writer.wait_closed(), timeout=2.0)

        self.assertEqual(await self._command(b"*2\r\n$3\r\nGET\r\n$6\r\nbefore\r\n"), b"$6\r\nbefore\r\n")
        self.assertTrue(Path(self.tmpdir.name, "dump.aof").exists())


if __name__ == "__main__":
    unittest.main()
