from __future__ import annotations

import asyncio
import os
from .commands import Dispatcher
from .persistence import AOF
from .resp import Decoder
from .store import Store


async def client(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, dispatcher: Dispatcher
) -> None:
    decoder = Decoder()
    try:
        while not reader.at_eof():
            data = await reader.read(65536)
            if not data:
                break
            for command in decoder.feed(data):
                reply, close = await dispatcher.dispatch(command)
                writer.write(reply)
                await writer.drain()
                if close:
                    return
    finally:
        writer.close()
        await writer.wait_closed()


async def run_server() -> None:
    store = Store()
    directory = os.environ.get("PYEDIS_DATA_DIR", "./data")
    fsync = os.environ.get("PYEDIS_AOF_FSYNC", "true").lower() == "true"
    aof = AOF(os.path.join(directory, "dump.aof"), fsync)
    aof.replay(store)
    port = int(os.environ.get("PORT", "6379"))
    server = await asyncio.start_server(
        lambda r, w: client(r, w, Dispatcher(store, aof)), "0.0.0.0", port
    )
    try:
        async with server:
            await server.serve_forever()
    finally:
        aof.close()


if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        pass
