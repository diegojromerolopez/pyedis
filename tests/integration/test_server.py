import asyncio
import unittest
from src.commands import CommandDispatcher
from src.main import handle_client
from src.store import Store


class TestServerIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.store = Store()
        self.dispatcher = CommandDispatcher(self.store)
        self.server = await asyncio.start_server(
            lambda r, w: handle_client(r, w, self.dispatcher),
            "127.0.0.1",
            0,
        )
        self.port = self.server.sockets[0].getsockname()[1]

    async def asyncTearDown(self) -> None:
        self.server.close()
        await self.server.wait_closed()

    async def test_raw_socket(self) -> None:
        reader, writer = await asyncio.open_connection("127.0.0.1", self.port)
        writer.write(b"PING\r\n")
        await writer.drain()
        data = await reader.read(100)
        self.assertEqual(data, b"+PONG\r\n")
        writer.close()
        await writer.wait_closed()


if __name__ == "__main__":
    unittest.main()
