"""Minimal asyncio TCP server implementing the PING walking skeleton."""

from __future__ import annotations

import asyncio
import os
import signal
from collections.abc import Awaitable, Callable

PING_RESP = b"+PONG\r\n"
RESP_PING = b"*1\r\n$4\r\nPING\r\n"


class ProtocolError(Exception):
    """Raised when a client sends an unsupported or malformed request."""


def parse_ping(request: bytes) -> bool:
    """Return whether request is one of the supported PING wire formats."""
    if request == b"PING\r\n":
        return True
    if request == RESP_PING:
        return True
    raise ProtocolError("expected PING")


async def client_session(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Serve requests on one connection until EOF or a protocol error."""
    try:
        while True:
            first = await reader.readline()
            if not first:
                break
            if first == b"PING\r\n":
                request = first
            elif first == b"*1\r\n":
                header = await reader.readline()
                if header != b"$4\r\n":
                    raise ProtocolError("expected PING")
                body = await reader.readexactly(6)
                request = first + header + body
            else:
                raise ProtocolError("expected PING")
            parse_ping(request)
            writer.write(PING_RESP)
            await writer.drain()
    except (ProtocolError, asyncio.IncompleteReadError, ConnectionError):
        pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except ConnectionError:
            pass


class Server:
    """Controllable asyncio server suitable for in-process integration tests."""

    def __init__(self, host: str = "127.0.0.1", port: int = 6379) -> None:
        self.host = host
        self.port = port
        self._server: asyncio.AbstractServer | None = None

    @property
    def address(self) -> tuple[str, int]:
        """Return the bound address, including an OS-selected ephemeral port."""
        if self._server is None or not self._server.sockets:
            raise RuntimeError("server is not started")
        host, port = self._server.sockets[0].getsockname()[:2]
        return str(host), int(port)

    async def start(self) -> tuple[str, int]:
        """Bind the listener and return its actual address."""
        if self._server is None:
            self._server = await asyncio.start_server(client_session, self.host, self.port)
            self.host, self.port = self.address
        return self.address

    async def stop(self) -> None:
        """Stop accepting connections and release the listening socket."""
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def serve_forever(self) -> None:
        """Run until cancelled while keeping the listener open."""
        if self._server is None:
            await self.start()
        assert self._server is not None
        await self._server.serve_forever()


async def run_server(host: str = "127.0.0.1", port: int | None = None) -> None:
    """Run the process server until SIGINT, SIGTERM, or cancellation."""
    selected_port = int(os.getenv("PORT", "6379")) if port is None else port
    server = Server(host, selected_port)
    await server.start()
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in ("SIGINT", "SIGTERM"):
        try:
            loop.add_signal_handler(getattr(signal, name), stopped.set)
        except (NotImplementedError, RuntimeError):
            continue
    try:
        await stopped.wait()
    finally:
        await server.stop()
