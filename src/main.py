import asyncio
import os
import sys
from src.store import Store
from src.persistence import AOFLogger
from src.commands import CommandDispatcher
from src.resp import RESPParser


async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    dispatcher: CommandDispatcher,
) -> None:
    parser = RESPParser()
    try:
        while not reader.at_eof():
            data = await reader.read(1024)
            if not data:
                break
            parser.feed(data)
            while True:
                args = parser.parse_one()
                if args is None:
                    break
                resp, close_conn = await dispatcher.dispatch(args)
                if resp:
                    writer.write(resp)
                    await writer.drain()
                if close_conn:
                    writer.close()
                    await writer.wait_closed()
                    return
    except Exception as e:
        sys.stderr.write(f"pyedis: client error {e}\n")
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


async def run_server() -> None:
    port = int(os.environ.get("PORT", "6379"))
    data_dir = os.environ.get("PYEDIS_DATA_DIR", "./data")
    fsync = os.environ.get("PYEDIS_AOF_FSYNC", "true").lower() == "true"

    store = Store()
    aof = AOFLogger(data_dir=data_dir, fsync=fsync)
    aof.replay(store)
    dispatcher = CommandDispatcher(store, aof)

    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, dispatcher), "0.0.0.0", port
    )
    sys.stdout.write(f"pyedis: server listening on port {port}\n")
    sys.stdout.flush()

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except (KeyboardInterrupt, SystemExit):
        sys.stdout.write("pyedis: shutting down\n")
