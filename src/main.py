from __future__ import annotations

import asyncio
import os
import signal
import sys

from .commands import Dispatcher
from .persistence import AOF
from .resp import Decoder
from .store import Store


async def client(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, dispatcher: Dispatcher
) -> None:
    decoder = Decoder()
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            for command in decoder.feed(data):
                reply = await dispatcher.dispatch(command)
                writer.write(reply)
                await writer.drain()
                if command and command[0].upper() == b"QUIT":
                    return
    finally:
        writer.close()
        await writer.wait_closed()


async def run_server() -> None:
    port = int(os.getenv("PORT", "6379"))
    data_dir = os.getenv("PYEDIS_DATA_DIR", "./data")
    fsync = os.getenv("PYEDIS_AOF_FSYNC", "true").lower() == "true"
    store = Store()
    aof = AOF(os.path.join(data_dir, "dump.aof"), fsync)
    await aof.replay(store)
    dispatcher = Dispatcher(store, aof)
    server = await asyncio.start_server(lambda r, w: client(r, w, dispatcher), "0.0.0.0", port)
    print(f"pyedis: listening on {port}")
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    async with server:
        await stop.wait()
    server.close()
    await server.wait_closed()


if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except Exception as exc:
        print(f"pyedis: {exc}", file=sys.stderr)
        raise SystemExit(1)
