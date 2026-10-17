"""Live server socket tests."""

import asyncio
import os
import tempfile
import unittest
from src.main import run_server


class TestServerIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.port = int(os.environ.get("SERVER_PORT", "0"))
        self.server_task = asyncio.create_task(
            run_server(host="127.0.0.1", port=self.port, data_dir=self.tmpdir.name, fsync=False)
        )

        deadline = asyncio.get_running_loop().time() + 2.0
        while True:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection("127.0.0.1", self.port), timeout=2.0
                )
                writer.close()
                await writer.wait_closed()
                break
            except (ConnectionRefusedError, OSError):
                if asyncio.get_running_loop().time() >= deadline:
                    self.fail("server did not become ready within 2 seconds")
                await asyncio.sleep(0.01)

            if self.port == 0:
                # A port of zero is selected by the OS; discover it from the
                # listening socket through the task's server is not possible,
                # so use a deterministic free-port fallback for this test.
                self.port = 16379

    async def asyncTearDown(self) -> None:
        self.server_task.cancel()
        try:
            await asyncio.wait_for(self.server_task, timeout=2.0)
        except asyncio.CancelledError:
            pass
        self.tmpdir.cleanup()

    async def test_socket_ping(self) -> None:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", self.port), timeout=2.0
        )
        try:
            writer.write(b"PING\r\n")
            await asyncio.wait_for(writer.drain(), timeout=2.0)
            response = await asyncio.wait_for(reader.readexactly(len(b"+PONG\r\n")), timeout=2.0)
            self.assertEqual(response, b"+PONG\r\n")
        finally:
            writer.close()
            await asyncio.wait_for(writer.wait_closed(), timeout=2.0)

    async def test_client_disconnect_does_not_stop_server(self) -> None:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", self.port), timeout=2.0
        )
        writer.close()
        await asyncio.wait_for(writer.wait_closed(), timeout=2.0)

        second_reader, second_writer = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", self.port), timeout=2.0
        )
        try:
            second_writer.write(b"PING\r\n")
            await asyncio.wait_for(second_writer.drain(), timeout=2.0)
            response = await asyncio.wait_for(second_reader.readexactly(7), timeout=2.0)
            self.assertEqual(response, b"+PONG\r\n")
        finally:
            second_writer.close()
            await asyncio.wait_for(second_writer.wait_closed(), timeout=2.0)


if __name__ == "__main__":
    unittest.main()
