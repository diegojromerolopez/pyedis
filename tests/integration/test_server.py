"""Integration tests with live TCP socket."""

import asyncio
import contextlib
import socket
import tempfile
import unittest

from src.main import run_server

TIMEOUT = 2.0


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestServerIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.port = _free_port()
        self.server_task = asyncio.create_task(
            run_server(host="127.0.0.1", port=self.port, data_dir=self.tmpdir.name, fsync=False)
        )
        await self._wait_for_server_ready()

    async def asyncTearDown(self) -> None:
        self.server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self.server_task
        self.tmpdir.cleanup()

    async def _wait_for_server_ready(self) -> None:
        deadline = asyncio.get_event_loop().time() + TIMEOUT
        last_exc: Exception | None = None
        while asyncio.get_event_loop().time() < deadline:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection("127.0.0.1", self.port), timeout=0.2
                )
                writer.close()
                await writer.wait_closed()
                return
            except OSError as exc:
                last_exc = exc
                await asyncio.sleep(0.05)
        raise AssertionError(f"server did not become ready in time: {last_exc}")

    async def _connect(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        return await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", self.port), timeout=TIMEOUT
        )

    async def test_ping_over_tcp(self) -> None:
        reader, writer = await self._connect()
        writer.write(b"PING\r\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(100), timeout=TIMEOUT)
        self.assertEqual(data, b"+PONG\r\n")
        writer.close()
        await writer.wait_closed()

    async def test_set_get_delete_round_trip_over_tcp(self) -> None:
        reader, writer = await self._connect()

        writer.write(b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(100), timeout=TIMEOUT)
        self.assertEqual(data, b"+OK\r\n")

        writer.write(b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(100), timeout=TIMEOUT)
        self.assertEqual(data, b"$3\r\nbar\r\n")

        writer.write(b"*2\r\n$3\r\nDEL\r\n$3\r\nfoo\r\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(100), timeout=TIMEOUT)
        self.assertEqual(data, b":1\r\n")

        writer.write(b"*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(100), timeout=TIMEOUT)
        self.assertEqual(data, b"$-1\r\n")

        writer.close()
        await writer.wait_closed()

    async def test_quit_closes_connection(self) -> None:
        reader, writer = await self._connect()
        writer.write(b"QUIT\r\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(100), timeout=TIMEOUT)
        self.assertEqual(data, b"+OK\r\n")
        # Server should close the connection after QUIT; further reads yield EOF.
        eof = await asyncio.wait_for(reader.read(100), timeout=TIMEOUT)
        self.assertEqual(eof, b"")
        writer.close()
        await writer.wait_closed()

    async def test_concurrent_clients_do_not_corrupt_state(self) -> None:
        async def set_and_get(key: str, value: str) -> bytes:
            reader, writer = await self._connect()
            set_cmd = (
                f"*3\r\n$3\r\nSET\r\n${len(key)}\r\n{key}\r\n${len(value)}\r\n{value}\r\n"
            ).encode()
            writer.write(set_cmd)
            await writer.drain()
            await asyncio.wait_for(reader.read(100), timeout=TIMEOUT)

            get_cmd = f"*2\r\n$3\r\nGET\r\n${len(key)}\r\n{key}\r\n".encode()
            writer.write(get_cmd)
            await writer.drain()
            reply = await asyncio.wait_for(reader.read(100), timeout=TIMEOUT)
            writer.close()
            await writer.wait_closed()
            return reply

        results = await asyncio.wait_for(
            asyncio.gather(
                set_and_get("k1", "v1"),
                set_and_get("k2", "v2"),
                set_and_get("k3", "v3"),
            ),
            timeout=TIMEOUT,
        )
        self.assertEqual(results[0], b"$2\r\nv1\r\n")
        self.assertEqual(results[1], b"$2\r\nv2\r\n")
        self.assertEqual(results[2], b"$2\r\nv3\r\n")

    async def test_persistence_across_server_restart(self) -> None:
        reader, writer = await self._connect()
        writer.write(b"*3\r\n$3\r\nSET\r\n$4\r\npkey\r\n$4\r\npval\r\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(100), timeout=TIMEOUT)
        self.assertEqual(data, b"+OK\r\n")
        writer.close()
        await writer.wait_closed()

        # Shut down the current server to flush/close AOF cleanly.
        self.server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self.server_task
        await asyncio.sleep(0.1)

        # Restart server on a new port using the same data directory.
        new_port = _free_port()
        self.port = new_port
        self.server_task = asyncio.create_task(
            run_server(host="127.0.0.1", port=new_port, data_dir=self.tmpdir.name, fsync=False)
        )
        await self._wait_for_server_ready()

        reader, writer = await self._connect()
        writer.write(b"*2\r\n$3\r\nGET\r\n$4\r\npkey\r\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(100), timeout=TIMEOUT)
        self.assertEqual(data, b"$4\r\npval\r\n")
        writer.close()
        await writer.wait_closed()


if __name__ == "__main__":
    unittest.main()
