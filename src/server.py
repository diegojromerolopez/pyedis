from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable


async def _handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    try:
        while line := await reader.readline():
            command = line.rstrip(b"\r\n").strip().upper()
            if command == b"PING":
                writer.write(b"+PONG\r\n")
            else:
                writer.write(b"-ERR unknown command\r\n")
            await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def run_server(
    host: str = "127.0.0.1",
    port: int | None = None,
    ready: asyncio.Event | None = None,
    stop: asyncio.Event | None = None,
    server_factory: Callable[
        ..., Awaitable[asyncio.AbstractServer]
    ] = asyncio.start_server,
) -> None:
    configured_port = int(os.environ.get("PORT", "6379")) if port is None else port
    server = await server_factory(_handle_client, host, configured_port)
    if ready is not None:
        ready.set()
    try:
        if stop is None:
            await asyncio.Event().wait()
        else:
            await stop.wait()
    finally:
        server.close()
        await server.wait_closed()
