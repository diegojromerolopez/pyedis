"""Asyncio TCP server implementation and client protocol handling."""

import asyncio
import os
import signal

from src.commands import CommandDispatcher
from src.persistence import AOFLogger, replay_aof
from src.resp import decode_resp_stream
from src.store import Store


async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    dispatcher: CommandDispatcher,
) -> None:
    buffer = bytearray()
    try:
        while data := await reader.read(4096):
            buffer.extend(data)
            commands, buffer = decode_resp_stream(buffer)
            for command in commands:
                reply, close_connection = await dispatcher.dispatch(command)
                writer.write(reply)
                await writer.drain()
                if close_connection:
                    return
    except (ConnectionError, asyncio.IncompleteReadError):
        pass
    finally:
        writer.close()
        await writer.wait_closed()


async def run_server(
    host: str = "0.0.0.0",
    port: int = 6379,
    data_dir: str = "./data",
    fsync: bool = True,
) -> None:
    os.makedirs(data_dir, exist_ok=True)
    aof = AOFLogger(os.path.join(data_dir, "dump.aof"), fsync=fsync)
    try:
        store = Store()
        replay_aof(aof.filepath, store)
        dispatcher = CommandDispatcher(store, aof)
        server = await asyncio.start_server(
            lambda reader, writer: handle_client(reader, writer, dispatcher), host, port
        )
        print(f"pyedis: listening on {host}:{server.sockets[0].getsockname()[1]}")
        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop_event.set)
            except (NotImplementedError, RuntimeError):
                pass
        async with server:
            try:
                await stop_event.wait()
            finally:
                server.close()
                await server.wait_closed()
    finally:
        aof.close()
        print("pyedis: shutting down cleanly")
