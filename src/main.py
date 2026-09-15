"""pyedis asynchronous server entry point."""
from __future__ import annotations

import asyncio
import os
import signal
import sys

from .commands import Commands
from .persistence import AOF
from .resp import Decoder, ProtocolError, error
from .store import Store


async def serve() -> None:
    port = int(os.environ.get("PORT", "6379")); directory = os.environ.get("PYEDIS_DATA_DIR", "./data")
    sync = os.environ.get("PYEDIS_AOF_FSYNC", "true").lower() in {"true", "1", "yes"}
    store, aof = Store(), AOF(directory, sync)
    aof.replay(store); commands = Commands(store, aof); lock = asyncio.Lock()
    clients: set[asyncio.StreamWriter] = set()
    async def client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        clients.add(writer); decoder = Decoder()
        try:
            while True:
                data = await reader.read(65536)
                if not data: decoder.finish(); break
                try: frames = decoder.feed(data)
                except ProtocolError:
                    writer.write(error("ERR protocol error")); await writer.drain(); break
                for frame in frames:
                    if not isinstance(frame, list): writer.write(error("ERR protocol error")); await writer.drain(); return
                    async with lock: reply, close = commands.run(frame)
                    writer.write(reply); await writer.drain()
                    if close: return
        except ProtocolError:
            writer.write(error("ERR protocol error")); await writer.drain()
        finally:
            clients.discard(writer); writer.close(); await writer.wait_closed()
    server = await asyncio.start_server(client, "127.0.0.1", port)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    async with server: await stop.wait()
    server.close(); await server.wait_closed()
    for writer in clients: writer.close()


def main() -> None:
    try: asyncio.run(serve())
    except Exception as exc:
        print(f"pyedis: {exc}", file=sys.stderr); raise SystemExit(1)


if __name__ == "__main__": main()
