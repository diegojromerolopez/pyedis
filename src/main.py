"""pyedis asyncio server entrypoint."""
from __future__ import annotations

import asyncio
import os
import signal
import sys
from .commands import Commands
from .persistence import Persistence
from .resp import Decoder, ProtocolError, encode, inline
from .store import Store


async def client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, commands: Commands, lock: asyncio.Lock) -> None:
    decoder = Decoder(); closing = False
    try:
        while not closing:
            data = await reader.read(65536)
            if not data: break
            frames = decoder.feed(data)
            if not frames and b"\r\n" in decoder.buffer and not decoder.buffer.startswith((b"*", b"$", b"+", b"-", b": " )):
                args = inline(decoder.buffer)
                if args is not None: decoder.buffer = b""; frames = [args]
            for frame in frames:
                if not isinstance(frame, list) or not all(isinstance(x, (bytes, str)) for x in frame):
                    writer.write(encode("ERR protocol error")); await writer.drain(); return
                args = [x if isinstance(x, bytes) else x.encode() for x in frame]
                async with lock: reply, closing = commands.execute(args)
                writer.write(encode(reply)); await writer.drain()
    except ProtocolError:
        writer.write(encode("ERR protocol error")); await writer.drain()
    finally:
        writer.close(); await writer.wait_closed()


async def serve() -> None:
    port = int(os.getenv("PORT", "6379")); directory = os.getenv("PYEDIS_DATA_DIR", "./data")
    fsync = os.getenv("PYEDIS_AOF_FSYNC", "true").lower() in ("true", "1", "yes")
    store = Store(); persistence = Persistence(directory, fsync); persistence.open()
    persistence.replay(store, print); commands = Commands(store, persistence); lock = asyncio.Lock()
    server = await asyncio.start_server(lambda r, w: client(r, w, commands, lock), "127.0.0.1", port)
    async with server: await server.serve_forever()


def main() -> None:
    try: asyncio.run(serve())
    except KeyboardInterrupt: return
    except Exception as exc:
        print(f"pyedis: {exc}", file=sys.stderr); raise SystemExit(1)


if __name__ == "__main__": main()
