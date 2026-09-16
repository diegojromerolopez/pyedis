from __future__ import annotations

import asyncio
import unittest

from src.server import Server


class ServerIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.server = Server(port=0)
        self.host, self.port = await self.server.start()

    async def asyncTearDown(self) -> None:
        await self.server.stop()

    async def test_inline_ping(self) -> None:
        reader, writer = await asyncio.open_connection(self.host, self.port)
        writer.write(b"PING\r\n")
        await writer.drain()
        self.assertEqual(await reader.readexactly(7), b"+PONG\r\n")
        writer.close()
        await writer.wait_closed()

    async def test_resp_array_ping(self) -> None:
        reader, writer = await asyncio.open_connection(self.host, self.port)
        writer.write(b"*1\r\n$4\r\nPING\r\n")
        await writer.drain()
        self.assertEqual(await reader.readexactly(7), b"+PONG\r\n")
        writer.close()
        await writer.wait_closed()

    async def test_stop_releases_listener(self) -> None:
        await self.server.stop()
        with self.assertRaises(OSError):
            await asyncio.open_connection(self.host, self.port)


if __name__ == "__main__":
    unittest.main()
