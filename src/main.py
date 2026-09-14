"""pyedis asyncio TCP entrypoint."""
from __future__ import annotations
import asyncio, os
from .commands import Dispatcher
from .persistence import AOF
from .resp import Decoder
from .store import Store

async def client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, dispatcher: Dispatcher) -> None:
    decoder = Decoder()
    try:
        while data := await reader.read(65536):
            for command in decoder.feed(data):
                reply, close = await dispatcher.dispatch(command)
                writer.write(reply); await writer.drain()
                if close: return
    finally:
        writer.close(); await writer.wait_closed()

async def run_server(host: str = '0.0.0.0', port: int | None = None) -> None:
    port = port if port is not None else int(os.getenv('PORT', '6379'))
    directory = os.getenv('PYEDIS_DATA_DIR', './data')
    aof = AOF(os.path.join(directory, 'dump.aof'), os.getenv('PYEDIS_AOF_FSYNC', 'true').lower() == 'true')
    store = Store(); await aof.replay(store); dispatcher = Dispatcher(store, aof)
    server = await asyncio.start_server(lambda r, w: client(r, w, dispatcher), host, port)
    try:
        async with server: await server.serve_forever()
    finally:
        aof.close(); server.close(); await server.wait_closed()

def main() -> None:
    try: asyncio.run(run_server())
    except KeyboardInterrupt: pass

if __name__ == '__main__': main()
