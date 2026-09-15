"""pyedis asynchronous TCP entry point."""
from __future__ import annotations

import asyncio
import os
import signal
from .commands import Commands
from .persistence import AOF
from .resp import Decoder, ProtocolError, encode
from .store import Store

async def client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, commands: Commands, lock: asyncio.Lock) -> None:
    decoder = Decoder()
    try:
        while True:
            data = await reader.read(65536)
            if not data: break
            try: frames = decoder.feed(data)
            except ProtocolError:
                writer.write(b'-ERR protocol error\r\n'); await writer.drain(); break
            for frame in frames:
                argv = frame.value if frame.kind == b'*' and isinstance(frame.value, list) else [frame.value]
                if not all(isinstance(x.value, bytes) for x in argv):
                    writer.write(b'-ERR protocol error\r\n'); break
                async with lock: reply, close = commands.run([x.value for x in argv])
                writer.write(reply); await writer.drain()
                if close: return
    finally:
        writer.close(); await writer.wait_closed()

async def serve() -> None:
    directory = os.getenv('PYEDIS_DATA_DIR', './data')
    aof = AOF(directory, os.getenv('PYEDIS_AOF_FSYNC', 'true').lower() in ('true','1','yes'))
    store = Store(); aof.load(store); commands = Commands(store, aof); lock = asyncio.Lock()
    server = await asyncio.start_server(lambda r, w: client(r, w, commands, lock), '127.0.0.1', int(os.getenv('PORT', '6379')))
    async with server: await server.serve_forever()

def main() -> None:
    try: asyncio.run(serve())
    except KeyboardInterrupt: return
    except Exception as exc:
        raise SystemExit(f'pyedis: {exc}')

if __name__ == '__main__': main()
