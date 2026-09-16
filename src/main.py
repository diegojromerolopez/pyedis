"""pyedis TCP server entry point."""
from __future__ import annotations

import asyncio
import os
import signal

from .commands import Dispatcher
from .persistence import AOF
from .resp import Decoder
from .store import Store


async def client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, dispatcher: Dispatcher) -> None:
    decoder = Decoder()
    try:
        while data := await reader.read(65536):
            for command in decoder.feed(data):
                reply, close = await dispatcher.execute(command)
                writer.write(reply)
                await writer.drain()
                if close:
                    return
    finally:
        writer.close()
        await writer.wait_closed()


async def run_server() -> None:
    data_dir = os.getenv("PYEDIS_DATA_DIR", "./data")
    port = int(os.getenv("PORT", "6379"))
    fsync = os.getenv("PYEDIS_AOF_FSYNC", "true").lower() == "true"
    store = Store()
    aof = AOF(os.path.join(data_dir, "dump.aof"), fsync)
    await aof.replay(store)
    server = await asyncio.start_server(lambda r, w: client(r, w, Dispatcher(store, aof)), "0.0.0.0", port)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        pass
