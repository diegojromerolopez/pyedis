"""Asyncio TCP server implementation and application configuration."""

import asyncio
import os
import sys

from src.commands import CommandDispatcher
from src.persistence import AOFLogger, replay_aof
from src.resp import decode_resp_stream
from src.store import Store


async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    dispatcher: CommandDispatcher,
) -> None:
    """Read, dispatch, and write RESP commands for one client connection."""
    buffer = bytearray()
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            buffer.extend(data)
            commands, remaining = decode_resp_stream(buffer)
            buffer = remaining
            for command in commands:
                response, should_close = await dispatcher.dispatch(command)
                writer.write(response)
                await writer.drain()
                if should_close:
                    return
    except (ConnectionError, asyncio.IncompleteReadError) as exc:
        print(f"pyedis: connection error {exc}", file=sys.stderr)
    except Exception as exc:
        print(f"pyedis: connection error {exc}", file=sys.stderr)
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except ConnectionError:
            pass


async def run_server(
    host: str = "0.0.0.0", port: int = 6379, data_dir: str = "./data", fsync: bool = True
) -> None:
    """Start the TCP server and serve until cancelled or stopped."""
    os.makedirs(data_dir, exist_ok=True)
    aof_path = os.path.join(data_dir, "dump.aof")
    store = Store()
    replay_aof(aof_path, store)
    dispatcher = CommandDispatcher(store, AOFLogger(aof_path, fsync=fsync))
    server = await asyncio.start_server(
        lambda reader, writer: handle_client(reader, writer, dispatcher), host, port
    )
    print(f"pyedis: listening on {host}:{port}", flush=True)
    try:
        async with server:
            await server.serve_forever()
    finally:
        server.close()
        await server.wait_closed()


async def run_from_environment() -> None:
    """Run the application using its environment-based configuration."""
    port = int(os.environ.get("PORT", "6379"))
    data_dir = os.environ.get("PYEDIS_DATA_DIR", "./data")
    fsync = os.environ.get("PYEDIS_AOF_FSYNC", "true").lower() == "true"
    await run_server(port=port, data_dir=data_dir, fsync=fsync)
