from __future__ import annotations

import asyncio
import os

from src.commands import Dispatcher
from src.persistence import AOF
from src.resp import Decoder
from src.store import Store


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
    store = Store()
    aof = AOF(os.getenv("PYEDIS_DATA_DIR", "./data"), os.getenv("PYEDIS_AOF_FSYNC", "true").lower() == "true")
    await aof.replay(store)
    dispatcher = Dispatcher(store, aof)
    server = await asyncio.start_server(lambda r, w: client(r, w, dispatcher), "0.0.0.0", int(os.getenv("PORT", "6379")))
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        pass
